from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .assets import load_manifest
from .archetypes import resolve_archetype
from .contracts import Issue, validate_diagram_model, validate_manifest, validate_source_model
from .intents import resolve_view_intent
from .model_v3 import is_v3_model, normalize_diagram_model, semantic_fingerprint
from .repository import verify_repository_evidence
from .registry import resolve_route, resolve_theme

if TYPE_CHECKING:
    from .extensions import ExtensionSet


def _kinds(model: dict[str, Any]) -> set[str]:
    return {str(node.get("kind", "")).lower() for node in model.get("nodes", [])}


def _text(model: dict[str, Any]) -> str:
    fields: list[str] = [str(model.get("title", "")), str(model.get("subtitle", ""))]
    for node in model.get("nodes", []):
        fields.extend(str(node.get(key, "")) for key in ("label", "kind", "description", "technology"))
        fields.extend(str(value) for value in node.get("tags", []))
    for edge in model.get("edges", []):
        fields.extend(str(edge.get(key, "")) for key in ("label", "kind", "protocol", "payload", "authority"))
        fields.extend(str(value) for value in edge.get("tags", []))
    for boundary in model.get("boundaries", []):
        fields.extend(str(boundary.get(key, "")) for key in ("label", "kind", "description"))
    return " ".join(fields).lower()


def _require_any(issues: list[Issue], haystack: set[str] | str, needles: set[str], code: str, message: str) -> None:
    found = bool(haystack & needles) if isinstance(haystack, set) else any(needle in haystack for needle in needles)
    if not found:
        issues.append(Issue("error", code, message, "profile"))


def _profile_checks(model: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    profile = str(model.get("route", {}).get("profile", ""))
    kinds = _kinds(model)
    text = _text(model)
    boundaries = model.get("boundaries", [])
    edges = model.get("edges", [])
    nodes = model.get("nodes", [])

    if profile.startswith("c4-"):
        expected_kind = {"c4-context": {"person", "actor", "system"}, "c4-container": {"container"}, "c4-component": {"component"}}[profile]
        _require_any(issues, kinds, expected_kind, "c4-element", f"{profile} needs its notation-specific C4 element type.")
        if profile == "c4-context" and not kinds.intersection({"person", "actor"}):
            issues.append(Issue("error", "c4-person", "C4 context needs at least one person/actor interacting with the system.", "nodes"))
        if profile in {"c4-container", "c4-component"} and not all(node.get("technology") for node in nodes if node.get("kind") not in {"person", "actor"}):
            issues.append(Issue("warning", "c4-technology", "C4 container/component nodes should state their technology.", "nodes"))

    if profile in {"sequence", "request-trace", "inference-trace", "auth-flow"}:
        if len(nodes) < 2 or not edges:
            issues.append(Issue("error", "interaction-participants", "Interaction diagrams require at least two participants and one message.", "nodes"))
        ordered = [edge.get("order", edge.get("layout", {}).get("order")) for edge in edges]
        if edges and any(value is None for value in ordered):
            issues.append(Issue("warning", "interaction-order", "Number every interaction with order or layout.order.", "edges"))
        if profile in {"request-trace", "inference-trace"} and not any(edge.get("protocol") for edge in edges):
            issues.append(Issue("warning", "protocol-missing", "Trace diagrams should label protocols or transports.", "edges"))

    if profile == "bpmn":
        _require_any(issues, kinds, {"start-event"}, "bpmn-start", "BPMN needs a start-event node.")
        _require_any(issues, kinds, {"end-event"}, "bpmn-end", "BPMN needs an end-event node.")
        if not boundaries:
            issues.append(Issue("warning", "bpmn-lanes", "BPMN should use pools or lanes for ownership.", "boundaries"))

    if profile == "state-machine":
        _require_any(issues, kinds, {"start-event", "initial-state"}, "state-initial", "State machines need an explicit initial state.")
        if any(not edge.get("label") for edge in edges):
            issues.append(Issue("warning", "state-transition-label", "State transitions should name their trigger or guard.", "edges"))

    if profile == "erd":
        if any(not node.get("fields") for node in nodes):
            issues.append(Issue("error", "erd-fields", "Every ERD entity needs fields with PK/FK notation.", "nodes"))
        if edges and any(not edge.get("label") for edge in edges):
            issues.append(Issue("error", "erd-cardinality", "Every ERD relationship needs an explicit cardinality label.", "edges"))

    if profile == "uml-class" and any(not node.get("fields") for node in nodes):
        issues.append(Issue("warning", "uml-members", "UML class nodes should list the attributes or operations relevant to this view.", "nodes"))

    if profile == "capability-map":
        _require_any(issues, kinds, {"capability"}, "capability-kind", "Capability maps need explicit capability nodes rather than application/process peers.")
    if profile == "value-stream" and (len(nodes) < 2 or not edges):
        issues.append(Issue("error", "value-stream-order", "Value streams need at least two ordered stages connected by value flow.", "profile"))
    if profile == "enterprise-landscape" and len(boundaries) < 2:
        issues.append(Issue("warning", "enterprise-layers", "Enterprise landscapes should separate at least two explicit viewpoints or layers.", "boundaries"))
    if profile == "stakeholder-map":
        _require_any(issues, kinds, {"stakeholder", "person", "actor", "organization"}, "stakeholder-kind", "Stakeholder maps need explicit stakeholder nodes.")
        if not any(node.get("importance") == "primary" for node in nodes):
            issues.append(Issue("error", "stakeholder-subject", "Stakeholder maps need a primary focal subject.", "nodes"))

    if profile in {"deployment", "cloud-reference", "kubernetes"} and not boundaries:
        issues.append(Issue("error", "runtime-boundary", "Runtime views need explicit environment, region, account, cluster, or namespace boundaries.", "boundaries"))
    if profile == "cloud-reference" and not any(node.get("assetRef") for node in nodes):
        issues.append(Issue("warning", "cloud-identities", "Cloud reference views should resolve exact service identities or deliberately use labeled generic glyphs.", "nodes"))
    if profile == "network-topology" and edges and any(not edge.get("protocol") for edge in edges):
        issues.append(Issue("warning", "network-protocol", "Network topology edges should label protocol/port when supported by evidence.", "edges"))
    if profile == "kubernetes":
        _require_any(issues, text, {"cluster", "namespace"}, "k8s-scope", "Kubernetes views need a cluster or namespace scope.")
        _require_any(issues, text, {"deployment", "statefulset", "daemonset", "pod", "workload", "service"}, "k8s-workload", "Kubernetes views need an explicit workload or service.")
    if profile == "integration" and edges and not any(edge.get("protocol") or edge.get("async") for edge in edges):
        issues.append(Issue("error", "integration-transport", "Integration views need protocol or asynchronous transport semantics.", "edges"))

    if profile in {"trust-boundary", "zero-trust", "threat-model", "data-classification"}:
        if not any("trust" in str(boundary.get("kind", "")).lower() or "trust" in str(boundary.get("label", "")).lower() for boundary in boundaries):
            issues.append(Issue("error", "trust-boundary", "Security architecture needs at least one explicit trust boundary.", "boundaries"))
        if profile == "zero-trust":
            _require_any(issues, text, {"identity", "policy", "authorize", "authentication"}, "zero-trust-control", "Zero-trust diagrams must show identity or policy enforcement.")
        if profile == "threat-model":
            _require_any(issues, text, {"threat", "mitigation", "risk", "stride"}, "threat-label", "Threat models must identify threats or mitigations.")

    if profile in {"rag", "agentic-rag"}:
        _require_any(issues, text, {"embed", "chunk", "ingest", "index"}, "rag-offline", "RAG diagrams need an offline ingestion/indexing path.")
        retrieval_nodes = " ".join(
            " ".join(str(node.get(key, "")) for key in ("label", "kind", "description"))
            for node in nodes
        ).lower()
        retrieval_edges = {str(edge.get("kind", "")).lower() for edge in edges}
        if not any(needle in retrieval_nodes for needle in {"retrieve", "retrieval", "search", "rerank"}) and not retrieval_edges.intersection({"retrieval", "read", "search", "query"}):
            issues.append(Issue("error", "rag-retrieval", "RAG diagrams need an explicit online retrieval operation or edge.", "profile"))
        _require_any(issues, text, {"generate", "generation", "llm", "model"}, "rag-generation", "RAG diagrams need generation/model synthesis.")
        if len(boundaries) < 2:
            issues.append(Issue("warning", "rag-boundaries", "Separate offline indexing and online serving into labeled boundaries.", "boundaries"))

    if profile in {"agent-orchestration", "agentic-rag"}:
        _require_any(issues, kinds, {"agent", "orchestrator"}, "agent-node", "Agent architecture needs an explicit agent or orchestrator node.")
        _require_any(issues, text, {"tool", "handoff", "delegate", "router"}, "agent-control", "Show tool use, routing, delegation, or handoff control.")

    if profile in {"mlops", "ml-lifecycle"}:
        _require_any(issues, text, {"train", "training", "experiment"}, "ml-training", "ML lifecycle diagrams need training or experimentation.")
        _require_any(issues, text, {"deploy", "serving", "inference", "registry"}, "ml-deployment", "ML lifecycle diagrams need registry, deployment, serving, or inference.")
        _require_any(issues, text, {"monitor", "drift", "evaluate", "metric"}, "ml-feedback", "ML lifecycle diagrams need evaluation or monitoring feedback.")

    if profile == "ai-solution-overview":
        _require_any(issues, kinds, {"actor", "person", "user"}, "ai-user", "AI solution overviews need a user or product actor.")
        _require_any(issues, kinds, {"model"}, "ai-model", "AI solution overviews need an explicit model boundary/component.")
    if profile == "eval-observability":
        _require_any(issues, text, {"eval", "metric", "judge", "review"}, "ai-evaluation", "AI evaluation views need evaluators or metrics.")
        _require_any(issues, text, {"trace", "production", "feedback", "monitor"}, "ai-observation", "AI evaluation views need production observation or feedback.")
    if profile == "ai-governance":
        _require_any(issues, text, {"owner", "accountable", "steward"}, "ai-owner", "AI governance needs explicit ownership/accountability.")
        _require_any(issues, text, {"policy", "control", "approval"}, "ai-control", "AI governance needs policy, control, or approval decisions.")
        _require_any(issues, text, {"monitor", "evidence", "audit", "incident"}, "ai-assurance", "AI governance needs ongoing evidence, monitoring, audit, or incident handling.")

    if profile == "observability":
        for signal in ("logs", "metrics", "traces"):
            if signal not in text:
                issues.append(Issue("warning", "observability-signal", f"Observability view does not show {signal}.", "profile"))

    if profile == "incident-response":
        _require_any(issues, text, {"detect", "triage", "contain", "recover", "review"}, "incident-lifecycle", "Incident response should show lifecycle stages.")

    if profile in {"ci-cd", "devsecops"}:
        _require_any(issues, text, {"build", "test"}, "pipeline-build-test", "Delivery pipelines should show build or test stages.")
        _require_any(issues, text, {"deploy", "release"}, "pipeline-deploy", "Delivery pipelines should show release or deployment.")

    if profile in {"streaming", "event-choreography"}:
        if not any(edge.get("async") or str(edge.get("kind", "")).lower() in {"async", "event", "publish", "subscribe"} for edge in edges):
            issues.append(Issue("error", "async-semantics", "Streaming/event diagrams need an explicitly asynchronous edge.", "edges"))

    if profile in {"etl-elt", "batch-pipeline", "lineage"}:
        _require_any(issues, text, {"source", "input", "producer", "raw"}, "data-source", "Data-flow views need an explicit source/input.")
        _require_any(issues, text, {"target", "output", "sink", "warehouse", "dataset", "store"}, "data-target", "Data-flow views need an explicit target/output.")
    if profile == "etl-elt":
        _require_any(issues, text, {"transform", "clean", "enrich", "load"}, "data-transform", "ETL/ELT views need an explicit transformation/load stage.")
    if profile == "lakehouse-medallion":
        for layer in ("bronze", "silver", "gold"):
            if layer not in text:
                issues.append(Issue("error", "medallion-layer", f"Lakehouse medallion view is missing the {layer} layer.", "profile"))

    if profile == "algorithm-flow":
        _require_any(issues, kinds, {"start-event", "input"}, "algorithm-start", "Algorithm flows need an explicit start/input.")
        _require_any(issues, kinds, {"end-event", "output"}, "algorithm-end", "Algorithm flows need an explicit end/output.")
    if profile == "user-flow":
        _require_any(issues, kinds, {"actor", "person", "user", "screen"}, "user-flow-entry", "User flows need a user or screen entry point.")
        _require_any(issues, text, {"success", "complete", "done", "failure", "error", "recover"}, "user-flow-outcome", "User flows need an explicit success/failure outcome.")
    if profile == "sitemap" and edges and len(edges) < len(nodes) - 1:
        issues.append(Issue("warning", "sitemap-hierarchy", "Sitemap nodes do not form a connected hierarchy.", "edges"))
    if profile == "service-blueprint" and len(boundaries) < 3:
        issues.append(Issue("error", "blueprint-lanes", "Service blueprints need customer, frontstage, and backstage/support lanes.", "boundaries"))

    if profile == "data-classification":
        _require_any(issues, text, {"public", "internal", "confidential", "restricted", "pii"}, "classification-label", "Data-classification diagrams need explicit classification labels.")

    return issues


def _intent_checks(model: dict[str, Any]) -> list[Issue]:
    intent = resolve_view_intent(model)
    nodes = model.get("nodes", [])
    edges = model.get("edges", [])
    boundaries = model.get("boundaries", [])
    kinds = _kinds(model)
    text = _text(model)
    issues: list[Issue] = []
    if len(nodes) < 2:
        issues.append(Issue("error", "intent-scope", f"A {intent} view requires at least two meaningful nodes.", "nodes"))
    if intent == "architecture":
        if not edges and not boundaries and str(model.get("route", {}).get("profile", "")) != "wireframe":
            issues.append(Issue("error", "architecture-structure", "Architecture views require at least one relationship or meaningful boundary.", "edges"))
    elif intent == "workflow":
        if not edges:
            issues.append(Issue("error", "workflow-path", "Workflow views require an ordered path between work steps.", "edges"))
        if not kinds.intersection({"decision", "gateway", "start-event", "end-event", "task", "process", "agent", "orchestrator"}):
            issues.append(Issue("warning", "workflow-steps", "Workflow views should contain explicit tasks, actors, events, or decisions rather than only structural services.", "nodes"))
    elif intent == "sequence":
        if not edges:
            issues.append(Issue("error", "sequence-messages", "Sequence views require at least one ordered message.", "edges"))
        unordered = [str(edge.get("id")) for edge in edges if edge.get("order", edge.get("layout", {}).get("order")) is None]
        if unordered:
            issues.append(Issue("error", "sequence-order", f"Sequence messages require order or layout.order: {', '.join(unordered)}.", "edges"))
    elif intent == "data-flow":
        if not edges:
            issues.append(Issue("error", "data-flow-path", "Data-flow views require directed movement between sources, transforms, stores, or consumers.", "edges"))
        has_data_edge = any(
            str(edge.get("lineClass", "")).lower() == "data"
            or str(edge.get("kind", "")).lower() in {"data", "read", "write", "stream", "publish", "consume", "transform", "retrieval"}
            or bool(edge.get("payload"))
            for edge in edges
        )
        if edges and not has_data_edge:
            issues.append(Issue("error", "data-flow-semantics", "At least one data-flow edge must name movement through kind, lineClass=data, or payload.", "edges"))
        _require_any(issues, text, {"source", "input", "producer", "raw", "ingest"}, "data-flow-source", "Data-flow views need an explicit source or producer.")
        _require_any(issues, text, {"store", "database", "warehouse", "consumer", "output", "sink", "index"}, "data-flow-destination", "Data-flow views need an explicit store, consumer, sink, or output.")
    elif intent == "lifecycle":
        _require_any(issues, kinds, {"start-event", "initial-state"}, "lifecycle-initial", "Lifecycle views need one explicit initial state.")
        _require_any(issues, kinds, {"end-event", "final-state", "terminal-state"}, "lifecycle-terminal", "Lifecycle views need at least one terminal state.")
        if not edges:
            issues.append(Issue("error", "lifecycle-transition", "Lifecycle views require state transitions.", "edges"))
        elif any(not str(edge.get("label", "")).strip() for edge in edges):
            issues.append(Issue("error", "lifecycle-trigger", "Every lifecycle transition must name its triggering event or condition.", "edges"))
    return issues


def _source_evidence_checks(model: dict[str, Any], source_model: dict[str, Any] | None) -> list[Issue]:
    if source_model is None:
        return [Issue("warning", "source-model-missing", "No source_model was supplied; factual traceability is unverified.", "sourceModel")]
    known = {str(item.get("id")) for item in source_model.get("facts", []) if isinstance(item, dict)}
    issues: list[Issue] = []
    for kind in ("nodes", "edges"):
        for index, item in enumerate(model.get(kind, [])):
            for reference in item.get("evidence", []):
                if reference not in known:
                    issues.append(Issue("error", "evidence-reference", f"Unknown evidence fact id: {reference}.", f"{kind}[{index}].evidence"))
    return issues


def _v3_provenance_checks(model: dict[str, Any], source_model: dict[str, Any] | None) -> list[Issue]:
    if not is_v3_model(model) or source_model is None:
        return []
    facts = {
        str(item.get("id")): str(item.get("confidence", "unknown"))
        for item in source_model.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    issues: list[Issue] = []
    semantics = model.get("semantics") if isinstance(model.get("semantics"), dict) else {}
    for key in ("groups", "entities", "relationships"):
        records = semantics.get(key, []) if isinstance(semantics, dict) else []
        for index, item in enumerate(records if isinstance(records, list) else []):
            if not isinstance(item, dict):
                continue
            for provenance_index, entry in enumerate(item.get("provenance", [])):
                if not isinstance(entry, dict):
                    continue
                fact_id = str(entry.get("factId", ""))
                if fact_id in facts and entry.get("confidence") != facts[fact_id]:
                    issues.append(
                        Issue(
                            "error",
                            "v3-provenance-confidence-drift",
                            f"Provenance confidence for {fact_id!r} does not match source_model ({facts[fact_id]!r}).",
                            f"semantics.{key}[{index}].provenance[{provenance_index}].confidence",
                        )
                    )
    return issues


def _asset_checks(model: dict[str, Any], project_root: Path | None, root: Path | None) -> list[Issue]:
    requested = {str(node.get("assetRef")) for node in model.get("nodes", []) if node.get("assetRef")}
    if not requested:
        return []
    if not project_root or not (project_root / "assets" / "asset_manifest.json").is_file():
        return [Issue("error", "asset-manifest-missing", "Nodes request assets but the project asset manifest is missing.", "assets")]
    manifest = load_manifest(project_root, root)
    issues = validate_manifest(manifest, project_root)
    by_key = {str(item.get("key")): item for item in manifest.get("assets", [])}
    for key in sorted(requested):
        asset = by_key.get(key)
        if not asset:
            issues.append(Issue("error", "asset-unresolved", f"Asset {key!r} is absent from asset_manifest.json.", "assets"))
        elif asset.get("state") == "NeedsManual":
            issues.append(Issue("error", "asset-manual", f"Asset {key!r} still needs manual resolution.", "assets"))
        elif asset.get("provider") != "drawio-native" and asset.get("state") not in {"Synced", "Embedded", "RenderVerified"}:
            issues.append(Issue("error", "asset-not-synced", f"Asset {key!r} is not synced or embedded.", "assets"))
    return issues


def _luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return 0.0
    channels = [int(value[index:index + 2], 16) / 255.0 for index in (0, 2, 4)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def _theme_checks(model: dict[str, Any], root: Path | None) -> list[Issue]:
    theme = resolve_theme(str(model.get("theme", "")), root)
    issues: list[Issue] = []
    for background in ("surface", "surfaceAlt", "canvas"):
        ratio = _contrast(str(theme["text"]), str(theme[background]))
        if ratio < 4.5:
            issues.append(Issue("error", "contrast", f"Theme text/{background} contrast is {ratio:.2f}:1; minimum is 4.5:1.", f"theme.{background}"))
    return issues


def _archetype_checks(model: dict[str, Any], project_root: Path | None, root: Path | None) -> list[Issue]:
    archetype = resolve_archetype(str(model.get("visualArchetype", "")) or None, root)
    if archetype.get("layoutAdapter") != "reference":
        return []
    issues: list[Issue] = []
    phases = [
        boundary for boundary in model.get("boundaries", [])
        if str(boundary.get("presentation", boundary.get("kind", ""))).lower() in {"phase-column", "outline-phase", "phase-row", "phase", "stage"}
    ]
    foundations = [
        boundary for boundary in model.get("boundaries", [])
        if str(boundary.get("presentation", boundary.get("kind", ""))).lower() in {"foundation-band", "foundation", "platform"}
    ]
    strategy = str(model.get("layoutStrategy", ""))
    phase_based = strategy in {"", "auto", "compact-pipeline", "phase-columns", "dense-phase-columns", "phase-rows"}
    if phase_based and len(phases) < 3:
        issues.append(Issue("warning", "reference-phases", "Reference-architecture views usually need at least three named phase columns.", "boundaries"))
    if not foundations and strategy != "compact-pipeline" and len(model.get("nodes", [])) > 10:
        issues.append(Issue("warning", "reference-foundation", "Add a foundation band for cross-cutting identity, security, operations, or governance capabilities.", "boundaries"))
    primary_edges = [edge for edge in model.get("edges", []) if edge.get("importance") == "primary"]
    if primary_edges:
        missing_steps = [str(edge.get("id")) for edge in primary_edges if edge.get("step") is None]
        if missing_steps:
            issues.append(Issue("warning", "reference-steps", f"Primary handoffs require step badges: {', '.join(missing_steps)}.", "edges"))
    else:
        steps = [edge for edge in model.get("edges", []) if edge.get("step") is not None]
        if model.get("edges") and len(steps) < max(1, len(model["edges"]) // 2):
            issues.append(Issue("warning", "reference-steps", "Number the main flow consistently, or mark primary handoffs explicitly so context edges may remain unnumbered.", "edges"))
    if archetype.get("officialIconRequired") and project_root and (project_root / "assets" / "asset_manifest.json").is_file():
        manifest = load_manifest(project_root, root)
        by_key = {str(item.get("key")): item for item in manifest.get("assets", [])}
        provider = str(archetype.get("provider", ""))
        icon_nodes = [node for node in model.get("nodes", []) if node.get("presentation", "service-icon") == "service-icon"]
        wrong = [
            str(node.get("id")) for node in icon_nodes
            if not node.get("assetRef") or by_key.get(str(node.get("assetRef")), {}).get("provider") != provider
        ]
        if wrong:
            issues.append(Issue("error", "reference-official-icons", f"Official provider icons are required for service-icon nodes: {', '.join(wrong)}.", "nodes"))
    return issues


def validate_drawio_metadata(drawio_path: Path, model: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    try:
        root = ET.parse(drawio_path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [Issue("error", "drawio-xml", f"Unable to parse draw.io XML: {exc}.", str(drawio_path))]
    if root.tag != "mxfile":
        issues.append(Issue("error", "drawio-root", "Root element must be mxfile.", str(drawio_path)))
        return issues
    canonical_model = model
    try:
        model = normalize_diagram_model(canonical_model)
    except ValueError as exc:
        return issues + [Issue("error", "diagram-model", str(exc), "diagram_model")]
    expected_route = f"{model['route']['family']}/{model['route']['profile']}"
    if root.get("nc-route") != expected_route:
        issues.append(Issue("error", "drawio-route", "Draw.io route metadata does not match diagram_model.", "mxfile@nc-route"))
    if root.get("nc-view-intent") != resolve_view_intent(model):
        issues.append(Issue("error", "drawio-view-intent", "Draw.io view intent metadata does not match diagram_model.", "mxfile@nc-view-intent"))
    expected_archetype = str(model.get("visualArchetype") or "technical-editorial")
    if root.get("nc-visual-archetype") != expected_archetype:
        issues.append(Issue("error", "drawio-archetype", "Draw.io visual archetype metadata does not match diagram_model.", "mxfile@nc-visual-archetype"))
    if is_v3_model(canonical_model):
        if root.get("nc-model-schema-version") != "3.0":
            issues.append(Issue("error", "drawio-model-version", "Draw.io metadata is not bound to diagram model schema 3.0.", "mxfile@nc-model-schema-version"))
        if root.get("nc-semantic-hash") != semantic_fingerprint(canonical_model):
            issues.append(Issue("error", "drawio-semantic-drift", "Draw.io semantic fingerprint does not match the canonical V3 semantics layer.", "mxfile@nc-semantic-hash"))
    cells = list(root.iter("mxCell"))
    ids = [cell.get("id", "") for cell in cells]
    if len(ids) != len(set(ids)):
        issues.append(Issue("error", "drawio-duplicate-id", "Draw.io contains duplicate mxCell ids.", "mxCell@id"))
    model_nodes = {str(node["id"]) for node in model.get("nodes", [])}
    drawn_nodes = {str(cell.get("nc-model-id")) for cell in cells if cell.get("nc-kind") == "node"}
    if model_nodes != drawn_nodes:
        issues.append(Issue("error", "drawio-node-drift", "Draw.io node ids do not match diagram_model.", "nodes"))
    has_title = any(cell.get("id") == "nc-title" or cell.get("nc-kind") == "title" for cell in cells)
    expects_title = bool(model.get("showTitle", True))
    if has_title != expects_title:
        issues.append(
            Issue(
                "error",
                "drawio-title-drift",
                "Draw.io title chrome does not match diagram_model.showTitle.",
                "showTitle",
            )
        )
    has_legend = any(cell.get("id") == "nc-legend" or cell.get("nc-kind") == "legend" for cell in cells)
    expects_legend = bool(model.get("legend"))
    if has_legend != expects_legend:
        issues.append(
            Issue(
                "error",
                "drawio-legend-drift",
                "Draw.io legend chrome does not match diagram_model.legend.",
                "legend",
            )
        )
    for cell in cells:
        style = cell.get("style", "")
        if re.search(r"image=https?://", style, re.IGNORECASE):
            issues.append(Issue("error", "remote-image", f"Cell {cell.get('id')} uses a remote image instead of an embedded asset.", cell.get("id", "")))
    return issues


def run_quality(
    model: dict[str, Any],
    source_model: dict[str, Any] | None = None,
    project_root: Path | None = None,
    drawio_path: Path | None = None,
    root: Path | None = None,
    repo_root: Path | None = None,
    extensions: "ExtensionSet | None" = None,
) -> list[Issue]:
    canonical_model = model
    issues = validate_diagram_model(canonical_model, root, extensions)
    if any(issue.severity == "error" for issue in issues):
        return issues
    model = normalize_diagram_model(canonical_model)
    route = resolve_route(model["route"]["family"], model["route"]["profile"], root, extensions)
    issues.extend(_intent_checks(model))
    issues.extend(_profile_checks(model))
    issues.extend(_source_evidence_checks(model, source_model))
    issues.extend(_v3_provenance_checks(canonical_model, source_model))
    if source_model is not None:
        issues.extend(validate_source_model(source_model))
        issues.extend(verify_repository_evidence(source_model, repo_root))
    issues.extend(_asset_checks(model, project_root, root))
    issues.extend(_theme_checks(model, root))
    issues.extend(_archetype_checks(model, project_root, root))
    if len(model.get("nodes", [])) > 18 and model.get("deliveryTarget") == "slide":
        issues.append(Issue("warning", "slide-density", "A slide-target diagram has more than 18 nodes; split or progressive-disclose it.", "nodes"))
    if drawio_path:
        issues.extend(validate_drawio_metadata(drawio_path, canonical_model))
    for rule in route.get("requiredChecks", []):
        if rule == "evidence" and source_model is None:
            issues.append(Issue("error", "profile-evidence", "This route requires a confirmed source_model.", "sourceModel"))
    if extensions is not None:
        for component in extensions.components("qa-rule"):
            result = extensions.run_hook(
                "qa-rule",
                component.component_id,
                {
                    "model": canonical_model,
                    "sourceModel": source_model,
                    "projectRoot": str(project_root.resolve()) if project_root else None,
                    "drawioPath": str(drawio_path.resolve()) if drawio_path else None,
                    "repoRoot": str(repo_root.resolve()) if repo_root else None,
                },
            )
            extension_issues = result.get("issues")
            if not isinstance(extension_issues, list):
                raise ValueError(f"QA extension {component.component_id} must return an issues array.")
            for index, value in enumerate(extension_issues):
                if not isinstance(value, dict):
                    raise ValueError(f"QA extension {component.component_id} issue {index} must be an object.")
                severity = value.get("severity")
                code = value.get("code")
                message = value.get("message")
                location = value.get("location", "")
                if severity not in {"error", "warning", "info"}:
                    raise ValueError(f"QA extension {component.component_id} issue {index} has invalid severity.")
                if not isinstance(code, str) or not code or not isinstance(message, str) or not message:
                    raise ValueError(f"QA extension {component.component_id} issue {index} requires code and message.")
                if not isinstance(location, str):
                    raise ValueError(f"QA extension {component.component_id} issue {index} location must be a string.")
                issues.append(Issue(severity, f"extension:{component.component_id}:{code}", message, location))
    return issues


def summarize(issues: list[Issue]) -> dict[str, Any]:
    counts = {severity: sum(issue.severity == severity for issue in issues) for severity in ("error", "warning", "info")}
    return {"ok": counts["error"] == 0, "counts": counts, "issues": [issue.to_dict() for issue in issues]}
