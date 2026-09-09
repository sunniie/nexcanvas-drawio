from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


STRATEGIES = (
    "compact-pipeline",
    "phase-columns",
    "dense-phase-columns",
    "phase-rows",
    "hybrid-grid",
    "hub-and-spoke",
    "nested-topology",
)

PHASE_PRESENTATIONS = {"phase-column", "outline-phase", "phase-row", "phase", "stage"}
TOPOLOGY_WORDS = {"region", "vnet", "virtual network", "subnet", "cluster", "account", "subscription", "deployment", "zone"}


def _presentation(boundary: dict[str, Any]) -> str:
    return str(boundary.get("presentation", boundary.get("kind", ""))).lower()


def _phase_boundaries(model: dict[str, Any]) -> list[dict[str, Any]]:
    phases = [
        boundary
        for boundary in model.get("boundaries", [])
        if not boundary.get("parent") and _presentation(boundary) in PHASE_PRESENTATIONS
    ]
    return sorted(phases, key=lambda item: (float(item.get("order", 10_000)), str(item.get("id", ""))))


def _graph_metrics(model: dict[str, Any]) -> dict[str, Any]:
    node_ids = [str(node["id"]) for node in model.get("nodes", [])]
    node_set = set(node_ids)
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    valid_edges: list[tuple[str, str]] = []
    for edge in model.get("edges", []):
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in node_set and target in node_set and source != target:
            outgoing[source].append(target)
            incoming[target].append(source)
            valid_edges.append((source, target))

    indegree = {node: len(incoming[node]) for node in node_ids}
    queue = deque(node for node in node_ids if indegree[node] == 0)
    visited = 0
    longest = {node: 1 for node in node_ids}
    while queue:
        source = queue.popleft()
        visited += 1
        for target in outgoing[source]:
            longest[target] = max(longest[target], longest[source] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    degree = {node: len(outgoing[node]) + len(incoming[node]) for node in node_ids}
    max_degree = max(degree.values(), default=0)
    branch_nodes = sum(1 for node in node_ids if len(outgoing[node]) > 1 or len(incoming[node]) > 1)
    cycle = visited < len(node_ids)
    return {
        "branchNodes": branch_nodes,
        "cycleDetected": cycle,
        "longestPath": max(longest.values(), default=0) if not cycle else None,
        "maxDegree": max_degree,
        "hubScore": round(max_degree / max(1, len(node_ids) - 1), 3) if len(node_ids) > 1 else 0.0,
    }


def analyze_model(model: dict[str, Any]) -> dict[str, Any]:
    nodes = list(model.get("nodes", []))
    edges = list(model.get("edges", []))
    boundaries = list(model.get("boundaries", []))
    phases = _phase_boundaries(model)
    nested = [boundary for boundary in boundaries if boundary.get("parent")]
    by_phase: dict[str, int] = defaultdict(int)
    phase_ids = {str(boundary["id"]) for boundary in phases}
    node_boundary = {str(node["id"]): str(node.get("boundary", "")) for node in nodes}
    for node in nodes:
        boundary = str(node.get("boundary", ""))
        if boundary in phase_ids:
            by_phase[boundary] += 1
        else:
            parent = next((str(item.get("parent")) for item in boundaries if str(item.get("id")) == boundary), "")
            if parent in phase_ids:
                by_phase[parent] += 1
    cross = sum(
        1
        for edge in edges
        if node_boundary.get(str(edge.get("source"))) != node_boundary.get(str(edge.get("target")))
    )
    ordered_phase = {str(item["id"]): index for index, item in enumerate(phases)}
    feedback = 0
    for edge in edges:
        source_boundary = node_boundary.get(str(edge.get("source")), "")
        target_boundary = node_boundary.get(str(edge.get("target")), "")
        source_phase = source_boundary if source_boundary in ordered_phase else next(
            (str(item.get("parent")) for item in boundaries if str(item.get("id")) == source_boundary), ""
        )
        target_phase = target_boundary if target_boundary in ordered_phase else next(
            (str(item.get("parent")) for item in boundaries if str(item.get("id")) == target_boundary), ""
        )
        if source_phase in ordered_phase and target_phase in ordered_phase and ordered_phase[target_phase] < ordered_phase[source_phase]:
            feedback += 1

    canvas = model.get("canvas", {})
    width = float(canvas.get("width", 1600))
    height = float(canvas.get("height", 900))
    labels = " ".join(str(boundary.get("label", "")).lower() for boundary in boundaries)
    topology_terms = sorted(term for term in TOPOLOGY_WORDS if term in labels)
    metrics = {
        "nodes": len(nodes),
        "edges": len(edges),
        "boundaries": len(boundaries),
        "phases": len(phases),
        "nestedBoundaries": len(nested),
        "containmentRatio": round(len(nested) / max(1, len(boundaries)), 3),
        "maxNodesPerPhase": max(by_phase.values(), default=0),
        "crossBoundaryEdges": cross,
        "crossBoundaryRatio": round(cross / max(1, len(edges)), 3),
        "feedbackEdges": feedback,
        "aspectRatio": round(width / max(height, 1), 3),
        "topologyTerms": topology_terms,
        **_graph_metrics(model),
    }
    return metrics


def _add(scores: dict[str, float], reasons: dict[str, list[str]], strategy: str, points: float, reason: str) -> None:
    scores[strategy] += points
    reasons[strategy].append(f"{points:+.1f}: {reason}")


def _phase_weights(model: dict[str, Any]) -> dict[str, float]:
    phases = _phase_boundaries(model)
    boundaries = list(model.get("boundaries", []))
    result: dict[str, float] = {}
    for phase in phases:
        phase_id = str(phase["id"])
        direct = sum(1 for node in model.get("nodes", []) if str(node.get("boundary", "")) == phase_id)
        children = [item for item in boundaries if str(item.get("parent", "")) == phase_id]
        child_nodes = sum(
            1
            for node in model.get("nodes", [])
            if str(node.get("boundary", "")) in {str(child["id"]) for child in children}
        )
        demand = direct + child_nodes + len(children) * 1.5
        result[phase_id] = round(max(0.7, min(2.2, 0.7 + demand * 0.12)), 2)
    return result


def brainstorm_layout(model: dict[str, Any]) -> dict[str, Any]:
    metrics = analyze_model(model)
    scores = {strategy: 0.0 for strategy in STRATEGIES}
    reasons: dict[str, list[str]] = {strategy: [] for strategy in STRATEGIES}

    if 3 <= metrics["phases"] <= 6:
        _add(scores, reasons, "compact-pipeline", 2.0, "three to six ordered phases")
        _add(scores, reasons, "phase-columns", 2.0, "ordered phase narrative")
    if metrics["nodes"] <= 10:
        _add(scores, reasons, "compact-pipeline", 4.0, "ten or fewer nodes")
    else:
        _add(scores, reasons, "compact-pipeline", -2.0, "node count exceeds sparse pipeline range")
    if metrics["branchNodes"] <= 2:
        _add(scores, reasons, "compact-pipeline", 2.0, "low branching")
    if metrics["phases"] >= 3 and metrics["feedbackEdges"] == 0:
        _add(scores, reasons, "phase-columns", 3.0, "ordered flow without phase feedback")
    if metrics["nodes"] >= 16:
        _add(scores, reasons, "dense-phase-columns", 4.0, "sixteen or more nodes")
    if metrics["maxNodesPerPhase"] >= 4:
        _add(scores, reasons, "dense-phase-columns", 3.0, "at least one dense phase")
    if metrics["nestedBoundaries"] >= 2 and metrics["phases"] >= 3:
        _add(scores, reasons, "dense-phase-columns", 2.0, "nested groups inside an ordered lifecycle")
    if metrics["feedbackEdges"] > 0:
        _add(scores, reasons, "hybrid-grid", 4.0, "phase feedback edges require two-dimensional routing")
        _add(scores, reasons, "phase-columns", -2.0, "feedback weakens a strict left-to-right lifecycle")
    if metrics["cycleDetected"]:
        _add(scores, reasons, "hybrid-grid", 3.0, "graph cycle detected")
    if metrics["hubScore"] >= 0.30:
        _add(scores, reasons, "hub-and-spoke", 5.0, "one node has high exchange centrality")
    if metrics["containmentRatio"] >= 0.30:
        _add(scores, reasons, "nested-topology", 4.0, "nested boundaries dominate the model")
    if metrics["topologyTerms"]:
        _add(scores, reasons, "nested-topology", 5.0, "topology scope terms appear in boundary labels")
    if metrics["aspectRatio"] <= 1.2 or str(model.get("direction", "LR")) in {"TB", "BT"}:
        _add(scores, reasons, "phase-rows", 7.0, "portrait or top-to-bottom target")
    elif metrics["phases"] >= 3:
        _add(scores, reasons, "phase-rows", -1.0, "landscape target favors columns")

    ranked = sorted(STRATEGIES, key=lambda item: (-scores[item], STRATEGIES.index(item)))
    automatic = ranked[0]
    explicit = str(model.get("layoutStrategy", "auto"))
    selected = automatic if explicit in {"", "auto"} else explicit
    orientation = "portrait" if selected == "phase-rows" else "landscape"
    foundation = any(
        _presentation(boundary) in {"foundation-band", "foundation", "platform"}
        for boundary in model.get("boundaries", [])
    )
    rails: list[str] = []
    if selected == "dense-phase-columns" and (metrics["crossBoundaryRatio"] >= 0.5 or metrics["edges"] >= 18):
        rails = ["top", "bottom"]
    elif selected in {"phase-columns", "hybrid-grid"} and metrics["feedbackEdges"]:
        rails = ["top"]
    risks: list[str] = []
    if metrics["feedbackEdges"] and selected in {"phase-columns", "dense-phase-columns"}:
        risks.append("Feedback edges may require a hybrid-grid override or a reserved return rail.")
    if metrics["nodes"] > 24:
        risks.append("High node count requires target-size label inspection and possible progressive disclosure.")
    if metrics["hubScore"] >= 0.30 and selected != "hub-and-spoke":
        risks.append("A high-centrality service exists but the selected layout does not place it as a hub.")
    if explicit not in {"", "auto"} and explicit != automatic:
        risks.append(f"Explicit strategy overrides automatic recommendation {automatic}.")

    return {
        "schemaVersion": "1.0",
        "metrics": metrics,
        "candidates": [
            {"strategy": strategy, "score": round(scores[strategy], 2), "reasons": reasons[strategy]}
            for strategy in ranked
        ],
        "automaticRecommendation": automatic,
        "selectedStrategy": selected,
        "selectionSource": "automatic" if selected == automatic and explicit in {"", "auto"} else "explicit-model",
        "geometryPlan": {
            "orientation": orientation,
            "phaseWeights": _phase_weights(model),
            "phaseTreatment": "outline" if selected == "compact-pipeline" else "filled-or-scope-based",
            "foundationBand": foundation,
            "reservedRails": rails,
            "stepPolicy": "badge primary handoffs; suffix parallel substeps; leave context edges unnumbered",
        },
        "manualReviewRisks": risks,
    }
