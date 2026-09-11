from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .extensions import ExtensionSet

from .common import load_json, sha256_json, utc_now, write_json
from .contracts import (
    validate_diagram_model,
    validate_lock,
    validate_repository_snapshot,
    validate_source_model,
    validate_sync_plan,
)
from .model_v3 import is_v3_model, semantic_fingerprint
from .repository_analysis import analyze_repository, diff_repository_snapshots


SYNC_PLAN_SCHEMA_VERSION = "1.0"
COLLECTIONS = ("groups", "entities", "relationships")
_MISSING = object()


def _require_valid(label: str, issues: list[Any]) -> None:
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ValueError(f"{label} is invalid: {errors[0].code}: {errors[0].message}")


def _empty_snapshot(source_base_id: str = "repository-sync") -> dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "analyzerVersion": "0.5.0",
        "sourceBaseId": source_base_id,
        "source": {},
        "scope": {},
        "files": [],
        "facts": [],
        "semanticProjection": {"groups": [], "entities": [], "relationships": []},
        "diagnostics": [],
        "fingerprint": "",
    }


def _map(records: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): item
        for item in records
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _json_value(value: Any) -> Any:
    return {"missing": True} if value is _MISSING else copy.deepcopy(value)


def _merge_record(
    collection: str,
    item_id: str,
    base: dict[str, Any],
    incoming: dict[str, Any],
    current: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    merged = copy.deepcopy(current)
    conflicts: list[dict[str, Any]] = []
    for field in sorted((set(base) | set(incoming) | set(current)) - {"id"}):
        old = base.get(field, _MISSING)
        new = incoming.get(field, _MISSING)
        user = current.get(field, _MISSING)
        if user == old:
            if new is _MISSING:
                merged.pop(field, None)
            else:
                merged[field] = copy.deepcopy(new)
        elif new == old or user == new:
            continue
        else:
            conflicts.append(
                {
                    "collection": collection,
                    "id": item_id,
                    "field": field,
                    "resolution": "preserve-current",
                    "baseline": _json_value(old),
                    "incoming": _json_value(new),
                    "current": _json_value(user),
                }
            )
    return merged, conflicts


def _removal_lookup(diff: dict[str, Any], collection: str) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): item
        for item in diff.get("changes", {}).get(collection, [])
        if isinstance(item, dict) and item.get("change") == "removed"
    }


def _merge_collection(
    collection: str,
    baseline: list[Any],
    incoming: list[Any],
    current: list[Any],
    diff: dict[str, Any],
    confirmed_removals: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], set[str], set[str]]:
    base_map = _map(baseline)
    incoming_map = _map(incoming)
    current_map = _map(current)
    removal_details = _removal_lookup(diff, collection)
    result = [copy.deepcopy(item) for item in current if isinstance(item, dict)]
    result_index = {str(item["id"]): index for index, item in enumerate(result) if isinstance(item.get("id"), str)}
    operations: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    added: set[str] = set()
    removed: set[str] = set()

    for item_id in sorted(set(base_map) | set(incoming_map)):
        base = base_map.get(item_id)
        new = incoming_map.get(item_id)
        user = current_map.get(item_id)
        if base is None and new is not None:
            if user is None:
                result_index[item_id] = len(result)
                result.append(copy.deepcopy(new))
                added.add(item_id)
                operations.append({"collection": collection, "id": item_id, "action": "add", "status": "safe"})
            elif user != new:
                conflicts.append(
                    {
                        "collection": collection,
                        "id": item_id,
                        "field": "*",
                        "resolution": "preserve-current",
                        "reason": "incoming-id-collides-with-user-record",
                    }
                )
            continue

        if base is not None and new is None:
            if user is None:
                continue
            detail = removal_details.get(item_id, {})
            if item_id in confirmed_removals:
                removed.add(item_id)
                operations.append(
                    {
                        "collection": collection,
                        "id": item_id,
                        "action": "remove",
                        "status": "confirmed",
                        "removalConfidence": detail.get("removalConfidence", "unknown"),
                    }
                )
            else:
                pending.append(
                    {
                        "collection": collection,
                        "id": item_id,
                        "action": "remove",
                        "status": "needs-confirmation",
                        "removalConfidence": detail.get("removalConfidence", "unknown"),
                        "reason": detail.get("reason", "source-removed"),
                    }
                )
            continue

        if base is None or new is None:
            continue
        if user is None:
            if new != base:
                conflicts.append(
                    {
                        "collection": collection,
                        "id": item_id,
                        "field": "*",
                        "resolution": "preserve-user-removal",
                        "reason": "source-and-user-both-changed",
                    }
                )
            else:
                operations.append(
                    {"collection": collection, "id": item_id, "action": "preserve-user-removal", "status": "safe"}
                )
            continue
        merged, record_conflicts = _merge_record(collection, item_id, base, new, user)
        conflicts.extend(record_conflicts)
        if merged != user:
            result[result_index[item_id]] = merged
            operations.append(
                {
                    "collection": collection,
                    "id": item_id,
                    "action": "update",
                    "status": "merged" if record_conflicts else "safe",
                }
            )

    if removed:
        result = [item for item in result if item.get("id") not in removed]
    return result, operations, conflicts, pending, added, removed


def _presentation_default(collection: str, item_id: str) -> dict[str, Any]:
    if collection == "relationships":
        return {
            "semanticId": item_id,
            "labelMode": "none",
            "lineClass": "dependency",
            "importance": "secondary",
        }
    return {"semanticId": item_id}


def _merge_presentation(
    presentation: dict[str, Any],
    additions: dict[str, set[str]],
    removals: dict[str, set[str]],
) -> dict[str, Any]:
    result = copy.deepcopy(presentation)
    for collection in COLLECTIONS:
        records = [item for item in result.get(collection, []) if isinstance(item, dict)]
        records = [item for item in records if item.get("semanticId") not in removals[collection]]
        existing = {str(item.get("semanticId")) for item in records}
        for item_id in sorted(additions[collection] - existing):
            records.append(_presentation_default(collection, item_id))
        result[collection] = records
    return result


def _fact_ids(model: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for collection in COLLECTIONS:
        for item in model.get("semantics", {}).get(collection, []):
            if not isinstance(item, dict):
                continue
            for provenance in item.get("provenance", []):
                if isinstance(provenance, dict) and isinstance(provenance.get("factId"), str):
                    result.add(provenance["factId"])
    return result


def _merge_source_model(
    source_model: dict[str, Any],
    baseline: dict[str, Any],
    incoming: dict[str, Any],
    merged_model: dict[str, Any],
) -> dict[str, Any]:
    result = copy.deepcopy(source_model)
    used_facts = _fact_ids(merged_model)
    baseline_fact_ids = {
        str(item.get("id")) for item in baseline.get("facts", []) if isinstance(item, dict) and item.get("id")
    }
    incoming_facts = {
        str(item["id"]): item for item in incoming.get("facts", []) if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    facts = [
        copy.deepcopy(item)
        for item in result.get("facts", [])
        if isinstance(item, dict) and (item.get("id") not in baseline_fact_ids or item.get("id") in used_facts)
    ]
    fact_index = {str(item.get("id")): index for index, item in enumerate(facts)}
    for fact_id in sorted(used_facts & set(incoming_facts)):
        if fact_id in fact_index:
            facts[fact_index[fact_id]] = copy.deepcopy(incoming_facts[fact_id])
        else:
            facts.append(copy.deepcopy(incoming_facts[fact_id]))
    result["facts"] = facts

    sources = [copy.deepcopy(item) for item in result.get("sources", []) if isinstance(item, dict)]
    incoming_source = incoming.get("source")
    if isinstance(incoming_source, dict):
        source_id = incoming_source.get("id")
        if source_id and any(
            isinstance(reference, dict) and reference.get("sourceId") == source_id
            for fact in facts
            for reference in fact.get("evidence", [])
            if isinstance(fact, dict)
        ):
            sources = [item for item in sources if item.get("id") != source_id]
            sources.append(copy.deepcopy(incoming_source))

    referenced_sources = {
        str(reference.get("sourceId"))
        for fact in facts
        if isinstance(fact, dict)
        for reference in fact.get("evidence", [])
        if isinstance(reference, dict) and reference.get("sourceId")
    }
    baseline_source = baseline.get("source", {})
    baseline_source_id = baseline_source.get("id") if isinstance(baseline_source, dict) else None
    if baseline_source_id and baseline_source_id not in referenced_sources:
        sources = [item for item in sources if item.get("id") != baseline_source_id]
    result["sources"] = sources
    return result


def build_sync_plan(
    project_root: Path,
    repo_root: Path,
    *,
    source_id: str = "repository-sync",
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_files: int | None = None,
    confirmed_removals: set[str] | None = None,
    extensions: ExtensionSet | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = project_root.resolve()
    current_model = load_json(project / "diagram_model.json")
    if not isinstance(current_model, dict) or not is_v3_model(current_model):
        raise ValueError("Incremental semantic sync requires Diagram Model schemaVersion '3.0'. Migrate V2 before syncing.")
    source_model = load_json(project / "source_model.json")
    lock = load_json(project / "diagram_lock.json")
    _require_valid("diagram_model.json", validate_diagram_model(current_model, extensions=extensions))
    _require_valid("source_model.json", validate_source_model(source_model))
    _require_valid("diagram_lock.json", validate_lock(lock, extensions=extensions))
    snapshot_path = project / "repository_snapshot.json"
    baseline = load_json(snapshot_path) if snapshot_path.is_file() else _empty_snapshot(source_id)
    if snapshot_path.is_file():
        _require_valid("repository_snapshot.json", validate_repository_snapshot(baseline))
    baseline_scope = baseline.get("scope", {}) if isinstance(baseline.get("scope"), dict) else {}
    effective_include = include if include is not None else baseline_scope.get("include")
    effective_exclude = exclude if exclude is not None else baseline_scope.get("exclude")
    effective_max = max_files if max_files is not None else int(baseline_scope.get("maxFiles", 500))
    incoming = analyze_repository(
        repo_root,
        source_id=str(baseline.get("sourceBaseId") or source_id),
        previous_snapshot=baseline if snapshot_path.is_file() else None,
        include=effective_include,
        exclude=effective_exclude,
        max_files=effective_max,
        extensions=extensions,
    )
    _require_valid("incoming repository snapshot", validate_repository_snapshot(incoming))
    diff = diff_repository_snapshots(baseline, incoming)
    confirmed = confirmed_removals or set()
    semantics = copy.deepcopy(current_model["semantics"])
    additions: dict[str, set[str]] = {name: set() for name in COLLECTIONS}
    removals: dict[str, set[str]] = {name: set() for name in COLLECTIONS}
    operations: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    base_projection = baseline.get("semanticProjection", {})
    incoming_projection = incoming.get("semanticProjection", {})
    for collection in COLLECTIONS:
        merged, collection_ops, collection_conflicts, collection_pending, added, removed = _merge_collection(
            collection,
            base_projection.get(collection, []) if isinstance(base_projection, dict) else [],
            incoming_projection.get(collection, []) if isinstance(incoming_projection, dict) else [],
            semantics.get(collection, []),
            diff,
            confirmed,
        )
        semantics[collection] = merged
        operations.extend(collection_ops)
        conflicts.extend(collection_conflicts)
        pending.extend(collection_pending)
        additions[collection] = added
        removals[collection] = removed

    merged_model = copy.deepcopy(current_model)
    merged_model["semantics"] = semantics
    merged_model["presentation"] = _merge_presentation(current_model["presentation"], additions, removals)
    merged_source = _merge_source_model(source_model, baseline, incoming, merged_model)
    merged_lock = copy.deepcopy(lock)
    merged_lock["sourceHash"] = sha256_json(merged_source)
    complete = not conflicts and not pending
    report = {
        "schemaVersion": SYNC_PLAN_SCHEMA_VERSION,
        "createdAt": utc_now(),
        "projectRoot": ".",
        "baselineFingerprint": baseline.get("fingerprint", ""),
        "incomingFingerprint": incoming.get("fingerprint", ""),
        "currentSemanticFingerprint": semantic_fingerprint(current_model),
        "mergedSemanticFingerprint": semantic_fingerprint(merged_model),
        "sourceRevision": incoming.get("source", {}).get("repository", {}).get("revision", ""),
        "summary": {
            "operations": len(operations),
            "conflicts": len(conflicts),
            "pendingRemovals": len(pending),
            "diagnostics": len(incoming.get("diagnostics", [])),
        },
        "complete": complete,
        "operations": operations,
        "conflicts": conflicts,
        "pendingRemovals": pending,
        "diff": diff,
    }
    _require_valid("merged diagram model", validate_diagram_model(merged_model, extensions=extensions))
    _require_valid("merged source model", validate_source_model(merged_source))
    _require_valid("merged diagram lock", validate_lock(merged_lock, extensions=extensions))
    _require_valid("semantic sync plan", validate_sync_plan(report))
    return report, incoming, merged_model, {"source": merged_source, "lock": merged_lock}


def sync_project(
    project_root: Path,
    repo_root: Path,
    *,
    dry_run: bool,
    source_id: str = "repository-sync",
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_files: int | None = None,
    confirmed_removals: set[str] | None = None,
    output: Path | None = None,
    extensions: ExtensionSet | None = None,
) -> dict[str, Any]:
    project = project_root.resolve()
    report, incoming, merged_model, companions = build_sync_plan(
        project,
        repo_root.resolve(),
        source_id=source_id,
        include=include,
        exclude=exclude,
        max_files=max_files,
        confirmed_removals=confirmed_removals,
        extensions=extensions,
    )
    report["mode"] = "dry-run" if dry_run else "apply"
    report["projectModified"] = False
    if dry_run:
        if output:
            write_json(output.resolve(), report)
        return report

    write_json(project / "diagram_model.json", merged_model)
    write_json(project / "source_model.json", companions["source"])
    write_json(project / "diagram_lock.json", companions["lock"])
    candidate_path = project / "reports" / "repository_snapshot.candidate.json"
    snapshot_target = project / "repository_snapshot.json" if report["complete"] else candidate_path
    write_json(snapshot_target, incoming)
    if report["complete"] and candidate_path.is_file():
        candidate_path.unlink()
    report["snapshot"] = str(snapshot_target.relative_to(project)).replace("\\", "/")
    report["projectModified"] = True
    report_path = output.resolve() if output else project / "reports" / "semantic_sync.json"
    write_json(report_path, report)
    return report
