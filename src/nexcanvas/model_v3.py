from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .common import load_json, sha256_json, write_json
from .intents import resolve_view_intent


V2_SCHEMA_VERSION = "2.0"
V3_SCHEMA_VERSION = "3.0"
CONFIDENCE_VALUES = {"confirmed", "inferred", "unknown"}


def is_v3_model(model: dict[str, Any]) -> bool:
    return model.get("schemaVersion") == V3_SCHEMA_VERSION


def semantic_fingerprint(model: dict[str, Any]) -> str:
    if not is_v3_model(model):
        raise ValueError("A semantics-only fingerprint requires diagram model schemaVersion '3.0'.")
    semantics = model.get("semantics")
    if not isinstance(semantics, dict):
        raise ValueError("V3 diagram model semantics must be an object.")
    canonical = copy.deepcopy(semantics)
    for key in ("groups", "entities", "relationships"):
        records = canonical.get(key)
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict):
                if isinstance(record.get("provenance"), list):
                    record["provenance"] = sorted(
                        record["provenance"],
                        key=lambda item: (
                            str(item.get("factId", "")) if isinstance(item, dict) else "",
                            str(item.get("confidence", "")) if isinstance(item, dict) else "",
                        ),
                    )
                if isinstance(record.get("tags"), list):
                    record["tags"] = sorted(record["tags"], key=str)
        canonical[key] = sorted(
            records,
            key=lambda item: str(item.get("id", "")) if isinstance(item, dict) else "",
        )
    return sha256_json(canonical)


def _provenance(references: Any, confidences: dict[str, str]) -> list[dict[str, str]]:
    if not isinstance(references, list):
        return []
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in references:
        if not isinstance(value, str) or not value or value in seen:
            continue
        seen.add(value)
        result.append({"factId": value, "confidence": confidences.get(value, "unknown")})
    return result


def _copy_fields(value: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: copy.deepcopy(value[field]) for field in fields if field in value}


def _extensions(value: dict[str, Any], claimed: set[str]) -> dict[str, Any]:
    return {key: copy.deepcopy(item) for key, item in value.items() if key not in claimed}


def source_confidences(source_model: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(source_model, dict):
        return {}
    values: dict[str, str] = {}
    for fact in source_model.get("facts", []):
        if not isinstance(fact, dict) or not isinstance(fact.get("id"), str):
            continue
        confidence = str(fact.get("confidence", "unknown"))
        values[fact["id"]] = confidence if confidence in CONFIDENCE_VALUES else "unknown"
    return values


def migrate_v2_model(model: dict[str, Any], source_model: dict[str, Any] | None = None) -> dict[str, Any]:
    if model.get("schemaVersion") != V2_SCHEMA_VERSION:
        raise ValueError(
            f"V2-to-V3 migration requires diagram model schemaVersion '2.0'; received {model.get('schemaVersion')!r}."
        )

    confidences = source_confidences(source_model)
    metadata_fields = (
        "title",
        "subtitle",
        "viewIntent",
        "route",
        "audience",
        "deliveryTarget",
        "language",
        "assumptions",
    )
    root_presentation_fields = (
        "theme",
        "visualArchetype",
        "layoutStrategy",
        "showTitle",
        "direction",
        "canvas",
        "legend",
    )
    boundary_semantic_fields = ("id", "label", "kind", "parent", "description", "tags")
    boundary_presentation_fields = ("presentation", "weight", "order", "layout")
    entity_semantic_fields = (
        "id",
        "label",
        "kind",
        "description",
        "caption",
        "technology",
        "fields",
        "tags",
    )
    entity_presentation_fields = ("boundary", "presentation", "assetRef", "importance", "layout")
    relationship_semantic_fields = (
        "id",
        "source",
        "target",
        "kind",
        "label",
        "protocol",
        "payload",
        "async",
        "authority",
        "trustCrossing",
        "annotation",
        "tags",
    )
    relationship_presentation_fields = (
        "labelMode",
        "labelPlacement",
        "laneId",
        "busId",
        "allowCrossing",
        "lineClass",
        "step",
        "importance",
        "layout",
    )

    metadata = _copy_fields(model, metadata_fields)
    metadata["viewIntent"] = resolve_view_intent(model)
    metadata.setdefault("language", "en")
    metadata.setdefault("assumptions", [])
    metadata["evidenceModel"] = str(model.get("sourceSnapshot") or "source_model.json")
    root_claimed = {
        "schemaVersion",
        "boundaries",
        "nodes",
        "edges",
        "sourceSnapshot",
        *metadata_fields,
        *root_presentation_fields,
    }
    root_extras = _extensions(model, root_claimed)
    if root_extras:
        metadata["extensions"] = root_extras

    groups: list[dict[str, Any]] = []
    group_views: list[dict[str, Any]] = []
    for item in model.get("boundaries", []):
        if not isinstance(item, dict):
            continue
        semantic = _copy_fields(item, boundary_semantic_fields)
        semantic["provenance"] = _provenance(item.get("evidence", []), confidences)
        claimed = {"evidence", *boundary_semantic_fields, *boundary_presentation_fields}
        extras = _extensions(item, claimed)
        if extras:
            semantic["extensions"] = extras
        groups.append(semantic)
        view = {"semanticId": item.get("id"), **_copy_fields(item, boundary_presentation_fields)}
        group_views.append(view)

    entities: list[dict[str, Any]] = []
    entity_views: list[dict[str, Any]] = []
    for item in model.get("nodes", []):
        if not isinstance(item, dict):
            continue
        semantic = _copy_fields(item, entity_semantic_fields)
        semantic["provenance"] = _provenance(item.get("evidence", []), confidences)
        claimed = {"evidence", *entity_semantic_fields, *entity_presentation_fields}
        extras = _extensions(item, claimed)
        if extras:
            semantic["extensions"] = extras
        entities.append(semantic)
        view = {"semanticId": item.get("id"), **_copy_fields(item, entity_presentation_fields)}
        entity_views.append(view)

    relationships: list[dict[str, Any]] = []
    relationship_views: list[dict[str, Any]] = []
    for item in model.get("edges", []):
        if not isinstance(item, dict):
            continue
        semantic = _copy_fields(item, relationship_semantic_fields)
        semantic["provenance"] = _provenance(item.get("evidence", []), confidences)
        claimed = {"evidence", *relationship_semantic_fields, *relationship_presentation_fields}
        extras = _extensions(item, claimed)
        if extras:
            semantic["extensions"] = extras
        relationships.append(semantic)
        view = {"semanticId": item.get("id"), **_copy_fields(item, relationship_presentation_fields)}
        relationship_views.append(view)

    presentation = _copy_fields(model, root_presentation_fields)
    presentation.setdefault("visualArchetype", "technical-editorial")
    presentation.setdefault("showTitle", True)
    presentation.setdefault("direction", "LR")
    presentation.setdefault("legend", [])
    presentation.update(
        {
            "groups": group_views,
            "entities": entity_views,
            "relationships": relationship_views,
        }
    )
    return {
        "schemaVersion": V3_SCHEMA_VERSION,
        "metadata": metadata,
        "semantics": {
            "groups": groups,
            "entities": entities,
            "relationships": relationships,
        },
        "presentation": presentation,
    }


def _by_semantic_id(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("semanticId")): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("semanticId"), str)
    }


def normalize_diagram_model(model: dict[str, Any]) -> dict[str, Any]:
    version = model.get("schemaVersion")
    if version == V2_SCHEMA_VERSION:
        return copy.deepcopy(model)
    if version != V3_SCHEMA_VERSION:
        raise ValueError(f"Unsupported diagram model schemaVersion {version!r}; expected '2.0' or '3.0'.")

    metadata = model.get("metadata")
    semantics = model.get("semantics")
    presentation = model.get("presentation")
    if not all(isinstance(value, dict) for value in (metadata, semantics, presentation)):
        raise ValueError("V3 diagram model requires metadata, semantics, and presentation objects.")
    assert isinstance(metadata, dict) and isinstance(semantics, dict) and isinstance(presentation, dict)

    group_views = _by_semantic_id(presentation.get("groups"))
    entity_views = _by_semantic_id(presentation.get("entities"))
    relationship_views = _by_semantic_id(presentation.get("relationships"))

    def evidence(item: dict[str, Any]) -> list[str]:
        return [
            str(entry["factId"])
            for entry in item.get("provenance", [])
            if isinstance(entry, dict) and isinstance(entry.get("factId"), str)
        ]

    boundaries: list[dict[str, Any]] = []
    for item in semantics.get("groups", []):
        if not isinstance(item, dict):
            continue
        semantic_id = str(item.get("id", ""))
        value = _copy_fields(item, ("id", "label", "kind", "parent", "description", "tags"))
        value.update(_copy_fields(group_views.get(semantic_id, {}), ("presentation", "weight", "order", "layout")))
        if evidence(item):
            value["evidence"] = evidence(item)
        boundaries.append(value)

    nodes: list[dict[str, Any]] = []
    for item in semantics.get("entities", []):
        if not isinstance(item, dict):
            continue
        semantic_id = str(item.get("id", ""))
        value = _copy_fields(
            item,
            ("id", "label", "kind", "description", "caption", "technology", "fields", "tags"),
        )
        value.update(
            _copy_fields(
                entity_views.get(semantic_id, {}),
                ("boundary", "presentation", "assetRef", "importance", "layout"),
            )
        )
        value["evidence"] = evidence(item)
        nodes.append(value)

    edges: list[dict[str, Any]] = []
    for item in semantics.get("relationships", []):
        if not isinstance(item, dict):
            continue
        semantic_id = str(item.get("id", ""))
        value = _copy_fields(
            item,
            (
                "id",
                "source",
                "target",
                "kind",
                "label",
                "protocol",
                "payload",
                "async",
                "authority",
                "trustCrossing",
                "annotation",
                "tags",
            ),
        )
        value.update(
            _copy_fields(
                relationship_views.get(semantic_id, {}),
                (
                    "labelMode",
                    "labelPlacement",
                    "laneId",
                    "busId",
                    "allowCrossing",
                    "lineClass",
                    "step",
                    "importance",
                    "layout",
                ),
            )
        )
        value["evidence"] = evidence(item)
        edges.append(value)

    result: dict[str, Any] = {
        "schemaVersion": V2_SCHEMA_VERSION,
        **_copy_fields(
            metadata,
            ("title", "subtitle", "viewIntent", "route", "audience", "deliveryTarget", "language", "assumptions"),
        ),
        **_copy_fields(
            presentation,
            ("theme", "visualArchetype", "layoutStrategy", "showTitle", "direction", "canvas", "legend"),
        ),
        "boundaries": boundaries,
        "nodes": nodes,
        "edges": edges,
        "sourceSnapshot": str(metadata.get("evidenceModel") or "source_model.json"),
    }
    return result


def migrate_file(
    input_path: Path,
    output_path: Path,
    *,
    source_path: Path | None = None,
    force: bool = False,
) -> dict[str, Any]:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if input_path == output_path:
        raise ValueError("Migration output must differ from the V2 input; in-place rewriting is not supported.")
    if output_path.exists() and not force:
        raise FileExistsError(f"Migration output already exists: {output_path}. Use --force to replace that output only.")
    source: dict[str, Any] | None = None
    effective_source = source_path.resolve() if source_path else input_path.with_name("source_model.json")
    if source_path is not None and not effective_source.is_file():
        raise FileNotFoundError(f"Explicit source model does not exist: {effective_source}")
    if effective_source.is_file():
        loaded = load_json(effective_source)
        if not isinstance(loaded, dict):
            raise ValueError("source_model.json must contain a JSON object.")
        source = loaded
    loaded_model = load_json(input_path)
    if not isinstance(loaded_model, dict):
        raise ValueError("diagram model must contain a JSON object.")
    from .contracts import validate_diagram_model, validate_source_model

    model_errors = [issue for issue in validate_diagram_model(loaded_model) if issue.severity == "error"]
    if model_errors:
        details = "; ".join(f"{issue.location}: {issue.message}" for issue in model_errors)
        raise ValueError(f"Cannot migrate an invalid V2 diagram model: {details}")
    if source is not None:
        source_errors = [issue for issue in validate_source_model(source) if issue.severity == "error"]
        if source_errors:
            details = "; ".join(f"{issue.location}: {issue.message}" for issue in source_errors)
            raise ValueError(f"Cannot use an invalid source model: {details}")
    migrated = migrate_v2_model(loaded_model, source)
    migrated_errors = [issue for issue in validate_diagram_model(migrated) if issue.severity == "error"]
    if migrated_errors:
        details = "; ".join(f"{issue.location}: {issue.message}" for issue in migrated_errors)
        raise RuntimeError(f"Migration produced an invalid V3 diagram model: {details}")
    write_json(output_path, migrated)
    return {
        "ok": True,
        "fromSchemaVersion": V2_SCHEMA_VERSION,
        "toSchemaVersion": V3_SCHEMA_VERSION,
        "input": str(input_path),
        "output": str(output_path),
        "sourceModel": str(effective_source) if source is not None else None,
        "groups": len(migrated["semantics"]["groups"]),
        "entities": len(migrated["semantics"]["entities"]),
        "relationships": len(migrated["semantics"]["relationships"]),
        "semanticFingerprint": semantic_fingerprint(migrated),
    }
