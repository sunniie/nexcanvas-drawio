from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from .common import portable_path, utc_now
from .contracts import Issue


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
    return completed.stdout.strip()


def _normalize_remote(value: str) -> str:
    remote = str(value).strip().replace("\\", "/")
    match = re.fullmatch(r"git@([^:]+):(.+)", remote)
    if match:
        remote = f"https://{match.group(1)}/{match.group(2)}"
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote.rstrip("/").lower()


def inspect_repository(repo_root: Path, source_id: str = "repository-1", relative_to: Path | None = None) -> dict[str, Any]:
    root = Path(_git(repo_root.resolve(), "rev-parse", "--show-toplevel")).resolve()
    revision = _git(root, "rev-parse", "HEAD")
    remote = _git(root, "remote", "get-url", "origin")
    dirty = bool(_git(root, "status", "--porcelain"))
    return {
        "id": source_id,
        "type": "repository",
        "location": portable_path(root, relative_to),
        "snapshot": revision,
        "repository": {
            "remote": remote,
            "revision": revision,
            "dirty": dirty,
            "capturedAt": utc_now(),
        },
    }


def _safe_repo_path(value: str) -> str | None:
    normalized = str(value).replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if not normalized or candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate.as_posix()


def verify_repository_evidence(source_model: dict[str, Any], repo_root: Path | None) -> list[Issue]:
    repository_sources = {
        str(source.get("id")): source
        for source in source_model.get("sources", [])
        if isinstance(source, dict) and source.get("type") == "repository"
    }
    if not repository_sources:
        return []
    if repo_root is None:
        return [Issue("error", "repository-root-required", "Repository-backed evidence requires --repo-root for Git verification.", "sourceModel.sources")]
    try:
        actual_root = Path(_git(repo_root.resolve(), "rev-parse", "--show-toplevel")).resolve()
        actual_remote = _git(actual_root, "remote", "get-url", "origin")
    except ValueError as exc:
        return [Issue("error", "repository-unavailable", f"Unable to inspect repository: {exc}", str(repo_root))]

    issues: list[Issue] = []
    verified_sources: dict[str, tuple[dict[str, Any], str]] = {}
    for source_id, source in repository_sources.items():
        repository = source.get("repository") if isinstance(source.get("repository"), dict) else {}
        remote = str(repository.get("remote", ""))
        revision = str(repository.get("revision", ""))
        if str(source.get("snapshot", "")) != revision:
            issues.append(Issue("error", "repository-snapshot", "Repository source snapshot must equal the pinned full revision.", f"sources.{source_id}.snapshot"))
            continue
        if _normalize_remote(remote) != _normalize_remote(actual_remote):
            issues.append(Issue("error", "repository-origin-mismatch", f"Pinned origin {remote!r} does not match local origin {actual_remote!r}.", f"sources.{source_id}.repository.remote"))
            continue
        try:
            resolved_revision = _git(actual_root, "rev-parse", f"{revision}^{{commit}}")
        except ValueError:
            issues.append(Issue("error", "repository-revision-missing", f"Pinned revision {revision!r} is not available in the local repository.", f"sources.{source_id}.repository.revision"))
            continue
        if resolved_revision.lower() != revision.lower():
            issues.append(Issue("error", "repository-revision-not-full", "Repository revision must be the full resolved commit hash.", f"sources.{source_id}.repository.revision"))
            continue
        verified_sources[source_id] = (source, revision)

    for fact_index, fact in enumerate(source_model.get("facts", [])):
        if not isinstance(fact, dict):
            continue
        for evidence_index, evidence in enumerate(fact.get("evidence", [])):
            if not isinstance(evidence, dict):
                continue
            source_id = str(evidence.get("sourceId", ""))
            if source_id not in repository_sources:
                continue
            location = f"facts[{fact_index}].evidence[{evidence_index}]"
            if source_id not in verified_sources:
                continue
            path = _safe_repo_path(str(evidence.get("path", "")))
            if path is None:
                issues.append(Issue("error", "repository-evidence-path", "Repository evidence path must be a non-empty repo-relative path without '..'.", f"{location}.path"))
                continue
            revision = verified_sources[source_id][1]
            try:
                content = _git(actual_root, "show", f"{revision}:{path}")
                blob = _git(actual_root, "rev-parse", f"{revision}:{path}")
            except ValueError:
                issues.append(Issue("error", "repository-evidence-missing", f"File {path!r} does not exist at revision {revision}.", f"{location}.path"))
                continue
            expected_blob = evidence.get("blob")
            if expected_blob and str(expected_blob).lower() != blob.lower():
                issues.append(Issue("error", "repository-blob-mismatch", f"Evidence blob for {path!r} does not match the pinned revision.", f"{location}.blob"))
            lines = content.splitlines()
            start = evidence.get("startLine")
            end = evidence.get("endLine", start)
            if start is not None:
                if not isinstance(start, int) or isinstance(start, bool) or start < 1:
                    issues.append(Issue("error", "repository-line-range", "startLine must be an integer >= 1.", f"{location}.startLine"))
                elif not isinstance(end, int) or isinstance(end, bool) or end < start or end > max(1, len(lines)):
                    issues.append(Issue("error", "repository-line-range", f"Evidence range {start}-{end} is outside {path!r} at the pinned revision ({len(lines)} lines).", location))
    return issues
