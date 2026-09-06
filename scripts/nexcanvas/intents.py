from __future__ import annotations

import re
from typing import Any


VIEW_INTENTS = ("architecture", "workflow", "sequence", "data-flow", "lifecycle")

DEFAULT_ROUTES: dict[str, tuple[str, str]] = {
    "architecture": ("software", "c4-container"),
    "workflow": ("behavior", "algorithm-flow"),
    "sequence": ("behavior", "sequence"),
    "data-flow": ("data", "etl-elt"),
    "lifecycle": ("behavior", "state-machine"),
}

PROFILE_DEFAULT_INTENTS: dict[tuple[str, str], str] = {
    **{("enterprise", profile): "architecture" for profile in ("capability-map", "enterprise-landscape", "stakeholder-map")},
    ("enterprise", "value-stream"): "workflow",
    **{("software", profile): "architecture" for profile in ("c4-context", "c4-container", "c4-component", "dependency", "uml-class")},
    **{("runtime-cloud", profile): "architecture" for profile in ("deployment", "cloud-reference", "network-topology", "kubernetes", "integration")},
    ("behavior", "sequence"): "sequence",
    ("behavior", "request-trace"): "sequence",
    ("behavior", "event-choreography"): "workflow",
    ("behavior", "bpmn"): "workflow",
    ("behavior", "state-machine"): "lifecycle",
    ("behavior", "algorithm-flow"): "workflow",
    ("data", "erd"): "architecture",
    **{("data", profile): "data-flow" for profile in ("etl-elt", "batch-pipeline", "streaming", "lineage", "lakehouse-medallion")},
    ("delivery-ops", "ci-cd"): "workflow",
    ("delivery-ops", "devsecops"): "workflow",
    ("delivery-ops", "observability"): "architecture",
    ("delivery-ops", "incident-response"): "workflow",
    ("security", "trust-boundary"): "architecture",
    ("security", "zero-trust"): "architecture",
    ("security", "auth-flow"): "sequence",
    ("security", "threat-model"): "architecture",
    ("security", "data-classification"): "architecture",
    ("ai-ml", "ai-solution-overview"): "architecture",
    ("ai-ml", "ml-lifecycle"): "lifecycle",
    ("ai-ml", "mlops"): "workflow",
    ("ai-ml", "rag"): "architecture",
    ("ai-ml", "agentic-rag"): "workflow",
    ("ai-ml", "agent-orchestration"): "architecture",
    ("ai-ml", "inference-trace"): "sequence",
    ("ai-ml", "eval-observability"): "architecture",
    ("ai-ml", "ai-governance"): "architecture",
    ("product-ui", "user-flow"): "workflow",
    ("product-ui", "sitemap"): "architecture",
    ("product-ui", "wireframe"): "architecture",
    ("product-ui", "service-blueprint"): "workflow",
}

PROFILE_COMPATIBILITY: dict[tuple[str, str], set[str]] = {
    (key[0], key[1]): {intent} for key, intent in PROFILE_DEFAULT_INTENTS.items()
}
PROFILE_COMPATIBILITY.update(
    {
        ("runtime-cloud", "integration"): {"architecture", "data-flow"},
        ("behavior", "event-choreography"): {"workflow", "data-flow", "sequence"},
        ("delivery-ops", "observability"): {"architecture", "data-flow"},
        ("delivery-ops", "incident-response"): {"workflow", "lifecycle"},
        ("ai-ml", "mlops"): {"architecture", "workflow", "data-flow", "lifecycle"},
        ("ai-ml", "rag"): {"architecture", "data-flow", "workflow"},
        ("ai-ml", "agentic-rag"): {"architecture", "workflow", "data-flow"},
        ("ai-ml", "agent-orchestration"): {"architecture", "workflow", "sequence"},
        ("ai-ml", "eval-observability"): {"architecture", "data-flow"},
        ("ai-ml", "ai-governance"): {"architecture", "workflow"},
        **{("data", profile): {"architecture", "data-flow"} for profile in ("etl-elt", "batch-pipeline", "streaming", "lineage", "lakehouse-medallion")},
    }
)

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "architecture": (
        "architecture", "kiến trúc", "system overview", "tổng quan hệ thống", "component", "service map",
        "topology", "deployment", "network", "boundary", "multi-agent system", "hệ thống multi-agent",
        "repo architecture", "codebase structure", "module boundaries",
    ),
    "workflow": (
        "workflow", "quy trình", "process", "steps", "các bước", "approval", "phê duyệt", "runbook",
        "ci/cd", "pipeline", "handoff", "thực hiện như thế nào", "from trigger to", "from request to",
        "business process", "approval flow", "step by step",
    ),
    "sequence": (
        "sequence", "request trace", "api call", "api request", "call chain", "gọi ai", "theo thời gian", "callback",
        "cache miss", "request lifecycle", "message order", "in what order", "message exchange", "who calls",
        "interaction order", "round trip",
    ),
    "data-flow": (
        "data flow", "dataflow", "luồng dữ liệu", "dữ liệu đi", "lineage", "etl", "elt", "streaming",
        "transform", "biến đổi", "source to", "producer", "consumer", "warehouse", "moves through",
        "move through", "flows through", "flow through", "where data", "request data", "payload", "read/write",
    ),
    "lifecycle": (
        "lifecycle", "state machine", "state transition", "trạng thái", "chuyển trạng thái", "status",
        "retry state", "cancelled", "terminal state", "vòng đời", "from created to", "status changes",
        "state changes", "valid states", "until completed",
    ),
}


def default_view_intent(family: str, profile: str) -> str:
    key = (str(family), str(profile))
    if key not in PROFILE_DEFAULT_INTENTS:
        raise KeyError(f"No view intent is registered for route {family}/{profile}.")
    return PROFILE_DEFAULT_INTENTS[key]


def resolve_view_intent(model: dict[str, Any]) -> str:
    explicit = str(model.get("viewIntent", "")).strip().lower()
    if explicit:
        return explicit
    route = model.get("route") if isinstance(model.get("route"), dict) else {}
    return default_view_intent(str(route.get("family", "")), str(route.get("profile", "")))


def compatible_view_intents(family: str, profile: str) -> set[str]:
    key = (str(family), str(profile))
    if key not in PROFILE_COMPATIBILITY:
        raise KeyError(f"No view intent compatibility is registered for route {family}/{profile}.")
    return set(PROFILE_COMPATIBILITY[key])


def classify_brief(brief: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", str(brief).strip().lower())
    scores = {intent: 0 for intent in VIEW_INTENTS}
    matches: dict[str, list[str]] = {intent: [] for intent in VIEW_INTENTS}
    for intent, phrases in _KEYWORDS.items():
        for phrase in phrases:
            if phrase in normalized:
                scores[intent] += 3 if " " in phrase or "/" in phrase else 1
                matches[intent].append(phrase)
    priority = ("sequence", "data-flow", "lifecycle", "workflow", "architecture")
    winner = max(priority, key=lambda intent: (scores[intent], -priority.index(intent)))
    if scores[winner] == 0:
        winner = "architecture"
    return {
        "viewIntent": winner,
        "scores": scores,
        "matches": {intent: values for intent, values in matches.items() if values},
        "confidence": "high" if scores[winner] >= 6 else "medium" if scores[winner] >= 3 else "low",
    }
