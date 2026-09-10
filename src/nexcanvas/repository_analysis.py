from __future__ import annotations

import ast
import copy
import fnmatch
import hashlib
import posixpath
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .common import sha256_json, utc_now
from .repository import inspect_repository


SNAPSHOT_SCHEMA_VERSION = "1.0"
ANALYZER_VERSION = "0.5.0"
SUPPORTED_SUFFIXES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}
DEFAULT_INCLUDE = ["**/*.py", "*.py", "**/*.js", "*.js", "**/*.jsx", "*.jsx", "**/*.mjs", "*.mjs", "**/*.cjs", "*.cjs", "**/*.ts", "*.ts", "**/*.tsx", "*.tsx", "**/*.mts", "*.mts", "**/*.cts", "*.cts"]
DEFAULT_EXCLUDE = ["**/node_modules/**", "**/.venv/**", "**/vendor/**", "**/dist/**", "**/build/**"]


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return completed.stdout


def _stable_id(prefix: str, *parts: str) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return f"repo-{prefix}-{hashlib.sha256(payload).hexdigest()[:16]}"


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _python_module(path: str) -> str:
    value = path[:-3].replace("/", ".")
    return value[:-9] if value.endswith(".__init__") else value


def _parse_python(content: str, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError as exc:
        return [], [], [
            {
                "severity": "warning",
                "code": "python-parse",
                "message": exc.msg,
                "path": path,
                "line": exc.lineno or 1,
            }
        ]
    symbols: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            symbols.append(
                {
                    "name": node.name,
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "line": node.lineno,
                    "exported": True,
                }
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"specifier": alias.name, "line": node.lineno, "relativeLevel": 0})
        elif isinstance(node, ast.ImportFrom):
            specifier = "." * node.level + (node.module or "")
            imports.append({"specifier": specifier, "line": node.lineno, "relativeLevel": node.level})
    return symbols, imports, []


_TS_SYMBOL_RE = re.compile(
    r"(?m)^\s*export\s+(?:default\s+)?(?:declare\s+)?(?:async\s+)?"
    r"(class|function|interface|type|enum|const|let|var)\s+([A-Za-z_$][\w$]*)"
)
_TS_IMPORT_RE = re.compile(
    r"(?m)^\s*(?:import|export)\s+(?:type\s+)?(?:[^\n;]*?\s+from\s+)?[\"']([^\"']+)[\"']"
)
_TS_REQUIRE_RE = re.compile(r"\b(?:require|import)\s*\(\s*[\"']([^\"']+)[\"']\s*\)")


def _line_for_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _parse_typescript(content: str, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    symbols = [
        {"name": match.group(2), "kind": match.group(1), "line": _line_for_offset(content, match.start()), "exported": True}
        for match in _TS_SYMBOL_RE.finditer(content)
    ]
    imports: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for expression in (_TS_IMPORT_RE, _TS_REQUIRE_RE):
        for match in expression.finditer(content):
            item = (match.group(1), _line_for_offset(content, match.start()))
            if item in seen:
                continue
            seen.add(item)
            imports.append({"specifier": item[0], "line": item[1]})
    return symbols, imports, []


def _python_target(source_path: str, specifier: str, modules: dict[str, str]) -> str | None:
    level = len(specifier) - len(specifier.lstrip("."))
    suffix = specifier[level:]
    if level:
        package = _python_module(source_path).split(".")
        if not source_path.endswith("/__init__.py"):
            package = package[:-1]
        keep = max(0, len(package) - level + 1)
        candidate = ".".join([*package[:keep], *([suffix] if suffix else [])]).strip(".")
    else:
        candidate = suffix
    while candidate:
        if candidate in modules:
            return modules[candidate]
        candidate = candidate.rsplit(".", 1)[0] if "." in candidate else ""
    return None


def _typescript_target(source_path: str, specifier: str, tracked: set[str]) -> str | None:
    if not specifier.startswith("."):
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), specifier))
    candidates = [base]
    for suffix in (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"):
        candidates.append(base + suffix)
        candidates.append(posixpath.join(base, "index" + suffix))
    return next((candidate for candidate in candidates if candidate in tracked), None)


def _previous_paths(snapshot: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(snapshot, dict):
        return {}
    result: dict[str, str] = {}
    projection = snapshot.get("semanticProjection", {})
    for entity in projection.get("entities", []) if isinstance(projection, dict) else []:
        if not isinstance(entity, dict):
            continue
        sync = entity.get("extensions", {}).get("repositorySync", {}) if isinstance(entity.get("extensions"), dict) else {}
        if isinstance(sync, dict) and isinstance(sync.get("path"), str) and isinstance(entity.get("id"), str):
            result[sync["path"]] = entity["id"]
    return result


def _rename_map(root: Path, previous: dict[str, Any] | None, revision: str) -> dict[str, str]:
    if not isinstance(previous, dict):
        return {}
    old = previous.get("source", {}).get("repository", {}).get("revision")
    if not isinstance(old, str) or not old or old == revision:
        return {}
    try:
        output = _git(root, "diff", "--name-status", "-M", old, revision, "--")
    except ValueError:
        return {}
    result: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R"):
            result[parts[2]] = parts[1]
    return result


def analyze_repository(
    repo_root: Path,
    *,
    source_id: str = "repository-sync",
    previous_snapshot: dict[str, Any] | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_files: int = 500,
) -> dict[str, Any]:
    if max_files < 1:
        raise ValueError("--max-files must be at least 1.")
    root = Path(_git(repo_root.resolve(), "rev-parse", "--show-toplevel").strip()).resolve()
    revision = _git(root, "rev-parse", "HEAD").strip()
    resolved_source_id = f"{source_id}-{revision[:12]}"
    source = inspect_repository(root, resolved_source_id)
    source["location"] = "."
    include_patterns = include or list(DEFAULT_INCLUDE)
    exclude_patterns = list(dict.fromkeys([*DEFAULT_EXCLUDE, *(exclude or [])]))
    paths = [
        path
        for path in _git(root, "ls-tree", "-r", "--name-only", revision).splitlines()
        if PurePosixPath(path).suffix.lower() in SUPPORTED_SUFFIXES
        and _matches(path, include_patterns)
        and not _matches(path, exclude_patterns)
    ]
    if len(paths) > max_files:
        raise ValueError(f"Repository analysis selected {len(paths)} files; increase --max-files above {max_files} or narrow --include.")

    previous_paths = _previous_paths(previous_snapshot)
    renames = _rename_map(root, previous_snapshot, revision)
    previous_files = {
        str(item.get("path")): item
        for item in (previous_snapshot or {}).get("files", [])
        if isinstance(item, dict) and item.get("path")
    }
    files: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for path in sorted(paths):
        content = _git(root, "show", f"{revision}:{path}")
        blob = _git(root, "rev-parse", f"{revision}:{path}").strip()
        language = SUPPORTED_SUFFIXES[PurePosixPath(path).suffix.lower()]
        if language == "python":
            symbols, imports, parser_diagnostics = _parse_python(content, path)
        else:
            symbols, imports, parser_diagnostics = _parse_typescript(content, path)
        diagnostics.extend(parser_diagnostics)
        previous_path = renames.get(path, path)
        if parser_diagnostics and previous_path in previous_files:
            symbols = copy.deepcopy(previous_files[previous_path].get("symbols", []))
            imports = [
                {key: copy.deepcopy(value) for key, value in item.items() if key != "targetPath"}
                for item in previous_files[previous_path].get("imports", [])
                if isinstance(item, dict)
            ]
        entity_id = previous_paths.get(previous_path) or previous_paths.get(path) or _stable_id("module", path)
        files.append(
            {
                "path": path,
                "language": language,
                "blob": blob,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "lineCount": max(1, len(content.splitlines())),
                "entityId": entity_id,
                "analysisConfidence": "unknown" if parser_diagnostics else "confirmed",
                "symbols": symbols,
                "imports": imports,
            }
        )

    tracked = {item["path"] for item in files}
    python_modules = {_python_module(path): path for path in tracked if path.endswith(".py")}
    by_path = {item["path"]: item for item in files}
    for item in files:
        for imported in item["imports"]:
            if item["language"] == "python":
                target = _python_target(item["path"], imported["specifier"], python_modules)
            else:
                target = _typescript_target(item["path"], imported["specifier"], tracked)
            if target:
                imported["targetPath"] = target

    facts: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    revision_key = revision[:12]
    for item in files:
        fact_id = f"repo-fact-{item['entityId']}-{revision_key}"
        confidence = item["analysisConfidence"]
        symbols = [f"{symbol['kind']} {symbol['name']}" for symbol in item["symbols"]]
        label_path = PurePosixPath(item["path"])
        label = label_path.parent.name if label_path.name == "__init__.py" else label_path.stem
        entities.append(
            {
                "id": item["entityId"],
                "label": label,
                "kind": "component",
                "description": f"{item['path']} · {len(symbols)} public symbol{'s' if len(symbols) != 1 else ''}",
                "technology": item["language"],
                "fields": symbols,
                "provenance": [{"factId": fact_id, "confidence": confidence}],
                "extensions": {
                    "repositorySync": {
                        "analyzer": item["language"],
                        "sourceKey": item["path"],
                        "path": item["path"],
                    }
                },
            }
        )
        facts.append(
            {
                "id": fact_id,
                "claim": (
                    f"The repository contains the {item['language']} module {item['path']} with {len(symbols)} public top-level symbols."
                    if confidence == "confirmed"
                    else f"The repository contains {item['path']}; its last known public symbols were retained because static parsing was ambiguous."
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "sourceId": resolved_source_id,
                        "path": item["path"],
                        "startLine": 1,
                        "endLine": item["lineCount"],
                        "blob": item["blob"],
                    }
                ],
            }
        )

    relationships: list[dict[str, Any]] = []
    seen_relationships: set[tuple[str, str]] = set()
    for item in files:
        for imported in item["imports"]:
            target_path = imported.get("targetPath")
            if not isinstance(target_path, str) or target_path not in by_path:
                continue
            source_entity = item["entityId"]
            target_entity = by_path[target_path]["entityId"]
            pair = (source_entity, target_entity)
            if pair in seen_relationships:
                continue
            seen_relationships.add(pair)
            relationship_id = _stable_id("import", source_entity, target_entity)
            fact_id = f"repo-fact-{relationship_id}-{revision_key}"
            confidence = item["analysisConfidence"]
            relationships.append(
                {
                    "id": relationship_id,
                    "source": source_entity,
                    "target": target_entity,
                    "kind": "dependency",
                    "label": "imports",
                    "provenance": [{"factId": fact_id, "confidence": confidence}],
                    "extensions": {
                        "repositorySync": {
                            "analyzer": item["language"],
                            "sourceKey": f"{item['path']}->{target_path}",
                            "path": item["path"],
                        }
                    },
                }
            )
            facts.append(
                {
                    "id": fact_id,
                    "claim": f"{item['path']} statically imports the internal module {target_path}.",
                    "confidence": confidence,
                    "evidence": [
                        {
                            "sourceId": resolved_source_id,
                            "path": item["path"],
                            "startLine": imported["line"],
                            "endLine": imported["line"],
                            "blob": item["blob"],
                        }
                    ],
                }
            )

    projection = {"groups": [], "entities": entities, "relationships": relationships}
    fingerprint_input = {
        "source": {"remote": source["repository"]["remote"], "revision": revision},
        "scope": {"include": include_patterns, "exclude": exclude_patterns},
        "files": files,
        "semanticProjection": projection,
        "facts": facts,
        "diagnostics": diagnostics,
    }
    return {
        "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
        "analyzerVersion": ANALYZER_VERSION,
        "createdAt": utc_now(),
        "sourceBaseId": source_id,
        "source": source,
        "scope": {
            "include": include_patterns,
            "exclude": exclude_patterns,
            "languages": sorted({item["language"] for item in files}),
            "maxFiles": max_files,
        },
        "files": files,
        "facts": facts,
        "semanticProjection": projection,
        "diagnostics": diagnostics,
        "fingerprint": sha256_json(fingerprint_input),
    }


def _record_map(snapshot: dict[str, Any], collection: str) -> dict[str, dict[str, Any]]:
    projection = snapshot.get("semanticProjection", {})
    values = projection.get(collection, []) if isinstance(projection, dict) else []
    return {str(item["id"]): item for item in values if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return sorted(key for key in set(before) | set(after) if key != "id" and before.get(key) != after.get(key))


def diff_repository_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_source = before.get("source", {})
    after_source = after.get("source", {})
    before_remote = str(before_source.get("repository", {}).get("remote", "")).lower().removesuffix(".git").rstrip("/")
    after_remote = str(after_source.get("repository", {}).get("remote", "")).lower().removesuffix(".git").rstrip("/")
    if before_remote and after_remote and before_remote != after_remote:
        raise ValueError("Repository snapshots must refer to the same normalized Git origin.")
    if before.get("sourceBaseId") and after.get("sourceBaseId") and before.get("sourceBaseId") != after.get("sourceBaseId"):
        raise ValueError("Repository snapshots must use the same sourceBaseId.")
    changes: dict[str, list[dict[str, Any]]] = {"groups": [], "entities": [], "relationships": []}
    diagnostics_by_path = {
        str(item.get("path"))
        for item in after.get("diagnostics", [])
        if isinstance(item, dict) and item.get("severity") in {"error", "warning"}
    }
    after_paths = {str(item.get("path")) for item in after.get("files", []) if isinstance(item, dict)}
    for collection in changes:
        old = _record_map(before, collection)
        new = _record_map(after, collection)
        for item_id in sorted(set(old) | set(new)):
            if item_id not in old:
                changes[collection].append({"id": item_id, "change": "added", "after": new[item_id]})
            elif item_id not in new:
                sync = old[item_id].get("extensions", {}).get("repositorySync", {})
                path = str(sync.get("path", "")) if isinstance(sync, dict) else ""
                confidence = "unknown" if path in diagnostics_by_path else "confirmed"
                reason = "analysis-ambiguous" if confidence == "unknown" else ("source-removed" if path not in after_paths else "semantic-removed")
                changes[collection].append(
                    {"id": item_id, "change": "removed", "removalConfidence": confidence, "reason": reason, "before": old[item_id]}
                )
            elif old[item_id] != new[item_id]:
                changes[collection].append(
                    {
                        "id": item_id,
                        "change": "changed",
                        "fields": _changed_fields(old[item_id], new[item_id]),
                        "before": old[item_id],
                        "after": new[item_id],
                    }
                )
    summary = {
        name: {
            kind: sum(1 for item in values if item["change"] == kind)
            for kind in ("added", "changed", "removed")
        }
        for name, values in changes.items()
    }
    return {
        "schemaVersion": "1.0",
        "fromRevision": before.get("source", {}).get("repository", {}).get("revision", ""),
        "toRevision": after.get("source", {}).get("repository", {}).get("revision", ""),
        "fromFingerprint": before.get("fingerprint", ""),
        "toFingerprint": after.get("fingerprint", ""),
        "summary": summary,
        "changes": changes,
        "diagnostics": after.get("diagnostics", []),
    }
