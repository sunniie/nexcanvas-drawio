from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .common import load_json
from .archetypes import resolve_archetype
from .layout import PRESENTATION_MIN_SIZES
from .intents import VIEW_INTENTS, compatible_view_intents, resolve_view_intent
from .registry import SUPPORTED_LAYOUTS, resolve_route, resolve_theme


ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
DELIVERY_TARGETS = {"readme", "engineering-doc", "slide", "poster", "print", "interactive"}
ASSET_STATES = {"Requested", "Resolved", "Synced", "Embedded", "RenderVerified", "NeedsManual"}
PIPELINE_STAGES = {"plan", "build", "diagram-qa", "render", "visual-qa", "postflight"}
PIPELINE_STAGE_STATES = {"pending", "running", "awaiting-review", "failed", "stale", "complete"}
LABEL_MODES = {"none", "offset", "callout", "note"}
LABEL_SIDES = {"auto", "above", "below", "left", "right", "center"}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    location: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _required_string(value: Any, field: str, issues: list[Issue]) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("error", "required-string", f"{field} must be a non-empty string.", field))


def _unique_ids(items: Iterable[dict[str, Any]], kind: str, issues: list[Issue]) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_id = item.get("id")
        location = f"{kind}[{index}].id"
        if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
            issues.append(Issue("error", "invalid-id", f"Invalid {kind} id: {item_id!r}.", location))
            continue
        if item_id in seen:
            issues.append(Issue("error", "duplicate-id", f"Duplicate id: {item_id}.", location))
        seen.add(item_id)
    return seen


def validate_diagram_model(model: dict[str, Any], root: Path | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if model.get("schemaVersion") != "2.0":
        issues.append(Issue("error", "schema-version", "diagram_model schemaVersion must be 2.0.", "schemaVersion"))
    _required_string(model.get("title"), "title", issues)
    _required_string(model.get("audience"), "audience", issues)
    if model.get("deliveryTarget") not in DELIVERY_TARGETS:
        issues.append(Issue("error", "delivery-target", f"Unsupported deliveryTarget: {model.get('deliveryTarget')!r}.", "deliveryTarget"))

    route = model.get("route") if isinstance(model.get("route"), dict) else {}
    try:
        route_entry = resolve_route(str(route.get("family", "")), str(route.get("profile", "")), root)
        if route_entry.get("layout") not in SUPPORTED_LAYOUTS:
            issues.append(Issue("error", "layout-adapter", f"Route uses unsupported layout {route_entry.get('layout')!r}.", "route"))
        view_intent = resolve_view_intent(model)
        if view_intent not in VIEW_INTENTS:
            issues.append(Issue("error", "view-intent", f"Unsupported viewIntent: {view_intent!r}.", "viewIntent"))
        elif view_intent not in compatible_view_intents(str(route.get("family", "")), str(route.get("profile", ""))):
            supported = ", ".join(sorted(compatible_view_intents(str(route.get("family", "")), str(route.get("profile", "")))))
            issues.append(Issue("error", "view-intent-route", f"viewIntent={view_intent!r} is not compatible with route {route.get('family')}/{route.get('profile')}; supported: {supported}.", "viewIntent"))
    except KeyError as exc:
        issues.append(Issue("error", "route", str(exc), "route"))

    try:
        resolve_theme(str(model.get("theme", "")), root)
    except KeyError as exc:
        issues.append(Issue("error", "theme", str(exc), "theme"))

    try:
        resolve_archetype(str(model.get("visualArchetype", "")) or None, root)
    except KeyError as exc:
        issues.append(Issue("error", "visual-archetype", str(exc), "visualArchetype"))

    canvas = model.get("canvas") if isinstance(model.get("canvas"), dict) else {}
    for field, minimum in (("width", 640), ("height", 480)):
        value = canvas.get(field)
        if not isinstance(value, int) or value < minimum:
            issues.append(Issue("error", "canvas", f"canvas.{field} must be an integer >= {minimum}.", f"canvas.{field}"))

    boundaries = model.get("boundaries", [])
    nodes = model.get("nodes", [])
    edges = model.get("edges", [])
    if not isinstance(boundaries, list):
        issues.append(Issue("error", "boundaries", "boundaries must be an array.", "boundaries"))
        boundaries = []
    if not isinstance(nodes, list) or not nodes:
        issues.append(Issue("error", "nodes", "nodes must be a non-empty array.", "nodes"))
        nodes = []
    if not isinstance(edges, list):
        issues.append(Issue("error", "edges", "edges must be an array.", "edges"))
        edges = []

    boundary_ids = _unique_ids((item for item in boundaries if isinstance(item, dict)), "boundaries", issues)
    node_ids = _unique_ids((item for item in nodes if isinstance(item, dict)), "nodes", issues)
    edge_ids = _unique_ids((item for item in edges if isinstance(item, dict)), "edges", issues)
    collisions = (boundary_ids & node_ids) | (boundary_ids & edge_ids) | (node_ids & edge_ids)
    for collision in sorted(collisions):
        issues.append(Issue("error", "cross-type-id", f"Id {collision} is reused across model object types.", collision))

    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            issues.append(Issue("error", "boundary-type", "Boundary must be an object.", f"boundaries[{index}]"))
            continue
        _required_string(boundary.get("label"), f"boundaries[{index}].label", issues)
        _required_string(boundary.get("kind"), f"boundaries[{index}].kind", issues)
        parent = boundary.get("parent")
        if parent and parent not in boundary_ids:
            issues.append(Issue("error", "boundary-parent", f"Boundary parent {parent!r} does not exist.", f"boundaries[{index}].parent"))

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(Issue("error", "node-type", "Node must be an object.", f"nodes[{index}]"))
            continue
        _required_string(node.get("label"), f"nodes[{index}].label", issues)
        _required_string(node.get("kind"), f"nodes[{index}].kind", issues)
        boundary = node.get("boundary")
        if boundary and boundary not in boundary_ids:
            issues.append(Issue("error", "node-boundary", f"Node boundary {boundary!r} does not exist.", f"nodes[{index}].boundary"))
        evidence = node.get("evidence", [])
        if evidence and (not isinstance(evidence, list) or not all(isinstance(value, str) and value for value in evidence)):
            issues.append(Issue("error", "node-evidence", "Node evidence must be an array of non-empty strings.", f"nodes[{index}].evidence"))
        layout = node.get("layout")
        if layout is not None and not isinstance(layout, dict):
            issues.append(Issue("error", "node-layout", "Node layout must be an object.", f"nodes[{index}].layout"))
        elif isinstance(layout, dict):
            presentation = str(node.get("presentation", "")).lower()
            minimum = PRESENTATION_MIN_SIZES.get(presentation)
            for dimension in ("width", "height"):
                value = layout.get(dimension)
                if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                    issues.append(Issue("error", "node-layout", f"layout.{dimension} must be numeric.", f"nodes[{index}].layout.{dimension}"))
                elif value is not None and minimum:
                    threshold = minimum[0] if dimension == "width" else minimum[1]
                    if value < threshold:
                        issues.append(
                            Issue(
                                "error",
                                "node-content-envelope",
                                f"{presentation} requires layout.{dimension} >= {threshold:g} to keep icon and text regions separate.",
                                f"nodes[{index}].layout.{dimension}",
                            )
                        )

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            issues.append(Issue("error", "edge-type", "Edge must be an object.", f"edges[{index}]"))
            continue
        if edge.get("source") not in node_ids:
            issues.append(Issue("error", "edge-source", f"Edge source {edge.get('source')!r} does not exist.", f"edges[{index}].source"))
        if edge.get("target") not in node_ids:
            issues.append(Issue("error", "edge-target", f"Edge target {edge.get('target')!r} does not exist.", f"edges[{index}].target"))
        _required_string(edge.get("kind"), f"edges[{index}].kind", issues)
        label_mode = edge.get("labelMode", "offset" if edge.get("label") or edge.get("annotation") else "none")
        if label_mode not in LABEL_MODES:
            issues.append(Issue("error", "edge-label-mode", f"Unsupported labelMode: {label_mode!r}.", f"edges[{index}].labelMode"))
        if label_mode != "none" and not any(str(edge.get(field, "")).strip() for field in ("label", "annotation")):
            issues.append(Issue("error", "edge-label-empty", f"labelMode={label_mode} requires label or annotation text.", f"edges[{index}].labelMode"))
        placement = edge.get("labelPlacement")
        if placement is not None and not isinstance(placement, dict):
            issues.append(Issue("error", "edge-label-placement", "labelPlacement must be an object.", f"edges[{index}].labelPlacement"))
        elif isinstance(placement, dict):
            side = placement.get("side")
            if side is not None and side not in LABEL_SIDES:
                issues.append(Issue("error", "edge-label-side", f"Unsupported labelPlacement.side: {side!r}.", f"edges[{index}].labelPlacement.side"))
            for field in ("segment", "t", "offset", "dx", "dy", "width", "height"):
                value = placement.get(field)
                if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                    issues.append(Issue("error", "edge-label-placement", f"labelPlacement.{field} must be numeric.", f"edges[{index}].labelPlacement.{field}"))
            if "segment" in placement and (not isinstance(placement.get("segment"), int) or isinstance(placement.get("segment"), bool)):
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.segment must be an integer.", f"edges[{index}].labelPlacement.segment"))
            elif isinstance(placement.get("segment"), int) and placement["segment"] < 0:
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.segment must be >= 0.", f"edges[{index}].labelPlacement.segment"))
            if isinstance(placement.get("t"), (int, float)) and not 0 <= placement["t"] <= 1:
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.t must be between 0 and 1.", f"edges[{index}].labelPlacement.t"))
            if isinstance(placement.get("offset"), (int, float)) and placement["offset"] < 0:
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.offset must be >= 0.", f"edges[{index}].labelPlacement.offset"))
            if isinstance(placement.get("width"), (int, float)) and placement["width"] < 24:
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.width must be >= 24.", f"edges[{index}].labelPlacement.width"))
            if isinstance(placement.get("height"), (int, float)) and placement["height"] < 16:
                issues.append(Issue("error", "edge-label-placement", "labelPlacement.height must be >= 16.", f"edges[{index}].labelPlacement.height"))
        for field in ("laneId", "busId"):
            value = edge.get(field)
            if value is not None and (not isinstance(value, str) or not ID_RE.fullmatch(value)):
                issues.append(Issue("error", "edge-route-id", f"{field} must be a valid model id.", f"edges[{index}].{field}"))
        if "allowCrossing" in edge and not isinstance(edge.get("allowCrossing"), bool):
            issues.append(Issue("error", "edge-crossing-flag", "allowCrossing must be boolean.", f"edges[{index}].allowCrossing"))
        edge_layout = edge.get("layout") if isinstance(edge.get("layout"), dict) else {}
        if any(key in edge_layout for key in ("labelOffsetX", "labelOffsetY")):
            issues.append(Issue("error", "retired-label-offset", "Use labelPlacement.side, offset and dx/dy instead of layout.labelOffsetX/Y.", f"edges[{index}].layout"))
        waypoints = edge_layout.get("waypoints")
        if waypoints is not None and (
            not isinstance(waypoints, list)
            or not waypoints
            or any(
                not isinstance(point, list)
                or len(point) != 2
                or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in point)
                for point in waypoints
            )
        ):
            issues.append(Issue("error", "edge-waypoints", "layout.waypoints must be a non-empty array of numeric [x, y] pairs.", f"edges[{index}].layout.waypoints"))
        if edge.get("source") == edge.get("target") and edge.get("kind") != "self-loop":
            issues.append(Issue("warning", "self-edge", "Self-edge should use kind=self-loop or be removed.", f"edges[{index}]"))

    return issues


def validate_source_model(model: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    if model.get("schemaVersion") != "2.0":
        issues.append(Issue("error", "schema-version", "source_model schemaVersion must be 2.0.", "schemaVersion"))
    if model.get("status") not in {"draft", "confirmed"}:
        issues.append(Issue("error", "status", "source_model status must be draft or confirmed.", "status"))
    sources = model.get("sources")
    source_ids: set[str] = set()
    repository_source_ids: set[str] = set()
    if not isinstance(sources, list):
        issues.append(Issue("error", "sources", "sources must be an array.", "sources"))
    else:
        source_ids = _unique_ids((item for item in sources if isinstance(item, dict)), "sources", issues)
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                issues.append(Issue("error", "source-type", "Source must be an object.", f"sources[{index}]"))
                continue
            _required_string(source.get("location"), f"sources[{index}].location", issues)
            source_type = source.get("type")
            if source_type not in {"repository", "document", "image", "url", "web", "conversation", "manual", "visual-reference"}:
                issues.append(Issue("error", "source-kind", f"Unsupported source type: {source_type!r}.", f"sources[{index}].type"))
            if source_type == "repository":
                if isinstance(source.get("id"), str):
                    repository_source_ids.add(source["id"])
                repository = source.get("repository") if isinstance(source.get("repository"), dict) else {}
                _required_string(repository.get("remote"), f"sources[{index}].repository.remote", issues)
                _required_string(repository.get("capturedAt"), f"sources[{index}].repository.capturedAt", issues)
                if not isinstance(repository.get("dirty"), bool):
                    issues.append(Issue("error", "repository-dirty", "Repository sources require a boolean dirty flag captured with the revision.", f"sources[{index}].repository.dirty"))
                revision = repository.get("revision")
                if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40,64}", revision):
                    issues.append(Issue("error", "repository-revision", "Repository sources require a full 40-64 character hexadecimal commit hash.", f"sources[{index}].repository.revision"))
                snapshot = source.get("snapshot")
                if not isinstance(snapshot, str) or snapshot != revision:
                    issues.append(Issue("error", "repository-snapshot", "Repository source snapshot must equal the pinned full revision.", f"sources[{index}].snapshot"))
    facts = model.get("facts")
    if not isinstance(facts, list):
        issues.append(Issue("error", "facts", "facts must be an array.", "facts"))
    else:
        _unique_ids((item for item in facts if isinstance(item, dict)), "facts", issues)
        for index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                continue
            _required_string(fact.get("claim"), f"facts[{index}].claim", issues)
            evidence = fact.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                issues.append(Issue("error", "fact-evidence", "Every fact requires at least one evidence reference.", f"facts[{index}].evidence"))
            elif isinstance(evidence, list):
                for evidence_index, reference in enumerate(evidence):
                    location = f"facts[{index}].evidence[{evidence_index}]"
                    if isinstance(reference, str):
                        if not reference.strip():
                            issues.append(Issue("error", "fact-evidence", "String evidence references must not be empty.", location))
                        elif any(reference.startswith(f"{source_id}:") for source_id in repository_source_ids):
                            issues.append(Issue("error", "repository-evidence-structured", "Repository evidence must use sourceId, repo-relative path, and an exact line range instead of a free-form string.", location))
                    elif isinstance(reference, dict):
                        source_id = reference.get("sourceId")
                        if source_id not in source_ids:
                            issues.append(Issue("error", "fact-evidence-source", f"Structured evidence refers to unknown source {source_id!r}.", f"{location}.sourceId"))
                        _required_string(reference.get("path"), f"{location}.path", issues)
                        start = reference.get("startLine")
                        end = reference.get("endLine")
                        if source_id in repository_source_ids and (start is None or end is None):
                            issues.append(Issue("error", "repository-evidence-range-required", "Repository evidence requires both startLine and endLine so release QA can verify the cited range.", location))
                        if start is not None and (not isinstance(start, int) or isinstance(start, bool) or start < 1):
                            issues.append(Issue("error", "fact-evidence-range", "startLine must be an integer >= 1.", f"{location}.startLine"))
                        if end is not None and (not isinstance(end, int) or isinstance(end, bool) or end < 1):
                            issues.append(Issue("error", "fact-evidence-range", "endLine must be an integer >= 1.", f"{location}.endLine"))
                        if isinstance(start, int) and isinstance(end, int) and end < start:
                            issues.append(Issue("error", "fact-evidence-range", "endLine must be >= startLine.", location))
                    else:
                        issues.append(Issue("error", "fact-evidence", "Evidence must be a string reference or structured repository range.", location))
            confidence = fact.get("confidence")
            if confidence is not None and confidence not in {"confirmed", "inferred", "unknown"}:
                issues.append(Issue("error", "fact-confidence", f"Unsupported confidence: {confidence!r}.", f"facts[{index}].confidence"))
    if not isinstance(model.get("assumptions"), list):
        issues.append(Issue("error", "assumptions", "assumptions must be an array.", "assumptions"))
    return issues


def validate_lock(lock: dict[str, Any], root: Path | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if lock.get("schemaVersion") != "2.0":
        issues.append(Issue("error", "schema-version", "diagram_lock schemaVersion must be 2.0.", "schemaVersion"))
    if lock.get("status") not in {"draft", "confirmed"}:
        issues.append(Issue("error", "status", "diagram_lock status must be draft or confirmed.", "status"))
    route = lock.get("route") if isinstance(lock.get("route"), dict) else {}
    try:
        resolve_route(str(route.get("family", "")), str(route.get("profile", "")), root)
        intent_model: dict[str, Any] = {"route": route}
        if lock.get("viewIntent"):
            intent_model["viewIntent"] = lock.get("viewIntent")
        view_intent = resolve_view_intent(intent_model)
        if view_intent not in compatible_view_intents(str(route.get("family", "")), str(route.get("profile", ""))):
            issues.append(Issue("error", "view-intent-route", f"Lock viewIntent={view_intent!r} is incompatible with its route.", "viewIntent"))
    except KeyError as exc:
        issues.append(Issue("error", "route", str(exc), "route"))
    try:
        resolve_theme(str(lock.get("theme", "")), root)
    except KeyError as exc:
        issues.append(Issue("error", "theme", str(exc), "theme"))
    try:
        resolve_archetype(str(lock.get("visualArchetype", "")) or None, root)
    except KeyError as exc:
        issues.append(Issue("error", "visual-archetype", str(exc), "visualArchetype"))
    decisions = lock.get("decisions") if isinstance(lock.get("decisions"), dict) else {}
    for field in ("audience", "deliveryTarget", "notation", "layout", "assetPolicy"):
        if field not in decisions:
            issues.append(Issue("error", "lock-decision", f"Missing locked decision: {field}.", f"decisions.{field}"))
    return issues


def validate_manifest(manifest: dict[str, Any], project_root: Path | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if manifest.get("schemaVersion") != "2.0":
        issues.append(Issue("error", "schema-version", "asset_manifest schemaVersion must be 2.0.", "schemaVersion"))
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return [Issue("error", "assets", "assets must be an array.", "assets")]
    keys: set[str] = set()
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            issues.append(Issue("error", "asset-type", "Asset must be an object.", f"assets[{index}]"))
            continue
        key = asset.get("key")
        _required_string(key, f"assets[{index}].key", issues)
        if key in keys:
            issues.append(Issue("error", "asset-key", f"Duplicate asset key: {key}.", f"assets[{index}].key"))
        if isinstance(key, str):
            keys.add(key)
        state = asset.get("state")
        if state not in ASSET_STATES:
            issues.append(Issue("error", "asset-state", f"Unsupported asset state: {state!r}.", f"assets[{index}].state"))
        local_path = asset.get("localPath")
        if state in {"Synced", "Embedded", "RenderVerified"}:
            if not isinstance(local_path, str) or not local_path:
                issues.append(Issue("error", "asset-path", f"Asset in state {state} requires localPath.", f"assets[{index}].localPath"))
            elif project_root and not (project_root / local_path).is_file():
                issues.append(Issue("error", "asset-missing", f"Asset file is missing: {local_path}.", f"assets[{index}].localPath"))
    return issues


def validate_project_state(state: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    if state.get("schemaVersion") != "1.0":
        issues.append(Issue("error", "schema-version", "project_state schemaVersion must be 1.0.", "schemaVersion"))
    if state.get("projectRoot") != ".":
        issues.append(Issue("error", "project-root", "project_state projectRoot must be '.'.", "projectRoot"))
    if state.get("status") not in {"pending", "running", "awaiting-review", "failed", "complete"}:
        issues.append(Issue("error", "pipeline-status", f"Unsupported pipeline status: {state.get('status')!r}.", "status"))
    _required_string(state.get("pipelineVersion"), "pipelineVersion", issues)
    stages = state.get("stages")
    if not isinstance(stages, dict):
        return issues + [Issue("error", "pipeline-stages", "project_state.stages must be an object.", "stages")]
    missing = PIPELINE_STAGES - set(stages)
    extra = set(stages) - PIPELINE_STAGES
    for name in sorted(missing):
        issues.append(Issue("error", "pipeline-stage-missing", f"Required pipeline stage is missing: {name}.", f"stages.{name}"))
    for name in sorted(extra):
        issues.append(Issue("error", "pipeline-stage-extra", f"Unknown pipeline stage: {name}.", f"stages.{name}"))
    hash_re = re.compile(r"^[0-9a-f]{64}$")
    for name in sorted(PIPELINE_STAGES & set(stages)):
        record = stages[name]
        if not isinstance(record, dict):
            issues.append(Issue("error", "pipeline-stage-type", "Pipeline stage must be an object.", f"stages.{name}"))
            continue
        if record.get("status") not in PIPELINE_STAGE_STATES:
            issues.append(Issue("error", "pipeline-stage-status", f"Unsupported stage status: {record.get('status')!r}.", f"stages.{name}.status"))
        attempts = record.get("attempts")
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
            issues.append(Issue("error", "pipeline-attempts", "Stage attempts must be an integer >= 0.", f"stages.{name}.attempts"))
        for field in ("inputHash", "outputHash"):
            value = record.get(field)
            if value is not None and (not isinstance(value, str) or not hash_re.fullmatch(value)):
                issues.append(Issue("error", "pipeline-hash", f"{field} must be a lowercase SHA-256 hash.", f"stages.{name}.{field}"))
        if record.get("status") == "complete" and not all(record.get(field) for field in ("inputHash", "outputHash", "outputs")):
            issues.append(Issue("error", "pipeline-complete-record", "A complete stage requires inputHash, outputHash, and outputs.", f"stages.{name}"))
    if state.get("status") == "complete" and any(
        not isinstance(stages.get(name), dict) or stages[name].get("status") != "complete"
        for name in PIPELINE_STAGES
    ):
        issues.append(Issue("error", "pipeline-false-complete", "A complete project requires every pipeline stage to be complete.", "status"))
    return issues


def validate_file(path: Path, kind: str, root: Path | None = None, project_root: Path | None = None) -> list[Issue]:
    value = load_json(path)
    if not isinstance(value, dict):
        return [Issue("error", "document-type", f"{kind} document must be a JSON object.", str(path))]
    if kind == "diagram-model":
        return validate_diagram_model(value, root)
    if kind == "source-model":
        return validate_source_model(value)
    if kind == "diagram-lock":
        return validate_lock(value, root)
    if kind == "asset-manifest":
        return validate_manifest(value, project_root)
    if kind == "project-state":
        return validate_project_state(value)
    raise ValueError(f"Unknown contract kind: {kind}")
