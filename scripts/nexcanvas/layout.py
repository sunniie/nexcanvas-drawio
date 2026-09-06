from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


PRESENTATION_MIN_SIZES: dict[str, tuple[float, float]] = {
    "service-icon": (150.0, 112.0),
    "compact-glyph": (126.0, 92.0),
    "service-tile": (160.0, 126.0),
    "note": (176.0, 76.0),
}


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass(frozen=True)
class EdgeRoute:
    points: tuple[tuple[float, float], ...]
    exit_x: float
    exit_y: float
    entry_x: float
    entry_y: float


@dataclass(frozen=True)
class LayoutResult:
    nodes: dict[str, Rect]
    boundaries: dict[str, Rect]
    edges: dict[str, EdgeRoute]
    adapter: str


def node_size(node: dict[str, Any]) -> tuple[float, float]:
    kind = str(node.get("kind", "service")).lower()
    description = str(node.get("description", ""))
    fields = node.get("fields") if isinstance(node.get("fields"), list) else []
    label = str(node.get("label", ""))
    presentation = str(node.get("presentation", "")).lower()
    width = 184.0
    height = 64.0
    if presentation in {"service-icon", "compact-glyph"}:
        width, height = (150.0, 112.0) if presentation == "service-icon" else (126.0, 92.0)
    elif presentation == "service-tile":
        width, height = 160.0, 126.0
    elif presentation == "note":
        width, height = 176.0, 76.0
    if description:
        width = min(280.0, max(196.0, 150.0 + min(100.0, len(description) * 1.3)))
        height = 82.0 if len(description) <= 70 else 98.0
    if fields:
        width = max(width, 230.0)
        height = max(height, 62.0 + 18.0 * len(fields))
    if kind in {"decision", "gateway"}:
        width, height = max(width, 150.0), max(height, 90.0)
    elif kind in {"actor", "person"}:
        width, height = 150.0, 78.0
    elif kind in {"datastore", "database", "dataset", "store"}:
        width, height = max(width, 184.0), max(height, 76.0)
    elif kind in {"event", "start-event", "end-event"}:
        width, height = max(128.0, len(label) * 7.0 + 36.0), 58.0
    if node.get("assetRef"):
        width = max(width, 210.0)
        height = max(height, 78.0)
    override = node.get("layout") if isinstance(node.get("layout"), dict) else {}
    width = float(override.get("width", width))
    height = float(override.get("height", height))
    minimum = PRESENTATION_MIN_SIZES.get(presentation)
    if minimum:
        # Presentation envelopes reserve independent icon and text bands. Apply
        # the floor last so kind-, description-, asset-, and user-level sizing
        # cannot collapse the label into the icon region.
        width = max(width, minimum[0])
        height = max(height, minimum[1])
    return width, height


def _preserve_presentation_envelope(node: dict[str, Any], width: float, height: float) -> tuple[float, float]:
    presentation = str(node.get("presentation", "")).lower()
    minimum = PRESENTATION_MIN_SIZES.get(presentation)
    if not minimum:
        return width, height
    return max(width, minimum[0]), max(height, minimum[1])


def _sort_key(item: dict[str, Any]) -> tuple[float, str]:
    layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
    order = layout.get("order", item.get("order", 10_000))
    try:
        order_value = float(order)
    except (TypeError, ValueError):
        order_value = 10_000.0
    return order_value, str(item.get("label", item.get("id", ""))).lower()


def _grid_positions(nodes: list[dict[str, Any]], area: Rect, columns: int | None = None) -> dict[str, Rect]:
    if not nodes:
        return {}
    ordered = sorted(nodes, key=_sort_key)
    columns = columns or max(1, math.ceil(math.sqrt(len(ordered) * max(area.w, 1) / max(area.h, 1))))
    columns = max(1, min(columns, len(ordered)))
    rows = math.ceil(len(ordered) / columns)
    gap_x = 26.0
    gap_y = 26.0
    cell_w = max(150.0, (area.w - gap_x * (columns - 1)) / columns)
    cell_h = max(72.0, (area.h - gap_y * (rows - 1)) / rows)
    result: dict[str, Rect] = {}
    for index, node in enumerate(ordered):
        row, column = divmod(index, columns)
        desired_w, desired_h = node_size(node)
        width = min(desired_w, max(120.0, cell_w - 4.0))
        height = min(desired_h, max(54.0, cell_h - 4.0))
        width, height = _preserve_presentation_envelope(node, width, height)
        x = area.x + column * (cell_w + gap_x) + (cell_w - width) / 2
        y = area.y + row * (cell_h + gap_y) + (cell_h - height) / 2
        result[str(node["id"])] = Rect(x, y, width, height)
    return result


def _topological_ranks(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    by_id = {str(node["id"]): node for node in nodes}
    indegree = {node_id: 0 for node_id in by_id}
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in by_id}
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in by_id and target in by_id and source != target:
            outgoing[source].append(target)
            indegree[target] += 1
    current = sorted((node_id for node_id, degree in indegree.items() if degree == 0), key=lambda item: _sort_key(by_id[item]))
    ranks: list[list[dict[str, Any]]] = []
    visited: set[str] = set()
    while current:
        ranks.append([by_id[node_id] for node_id in current])
        next_ids: list[str] = []
        for node_id in current:
            visited.add(node_id)
            for target in outgoing[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    next_ids.append(target)
        current = sorted(set(next_ids), key=lambda item: _sort_key(by_id[item]))
    remaining = sorted((node for node_id, node in by_id.items() if node_id not in visited), key=_sort_key)
    if remaining:
        ranks.append(remaining)
    return ranks or [sorted(nodes, key=_sort_key)]


def _layered_positions(model: dict[str, Any], area: Rect, tree: bool = False) -> dict[str, Rect]:
    nodes = list(model.get("nodes", []))
    ranks = _topological_ranks(nodes, list(model.get("edges", [])))
    direction = "TB" if tree else str(model.get("direction", "LR"))
    result: dict[str, Rect] = {}
    if direction in {"TB", "BT"}:
        layer_h = area.h / max(1, len(ranks))
        rank_iter = list(reversed(ranks)) if direction == "BT" else ranks
        for rank_index, rank in enumerate(rank_iter):
            row_area = Rect(area.x, area.y + rank_index * layer_h, area.w, layer_h)
            result.update(_grid_positions(rank, row_area, columns=len(rank)))
    else:
        layer_w = area.w / max(1, len(ranks))
        rank_iter = list(reversed(ranks)) if direction == "RL" else ranks
        for rank_index, rank in enumerate(rank_iter):
            column_area = Rect(area.x + rank_index * layer_w, area.y, layer_w, area.h)
            result.update(_grid_positions(rank, column_area, columns=1))
    return result


def _radial_positions(nodes: list[dict[str, Any]], area: Rect) -> dict[str, Rect]:
    if not nodes:
        return {}
    ordered = sorted(nodes, key=lambda node: (0 if node.get("importance") == "primary" else 1, *_sort_key(node)))
    center = ordered[0]
    center_w, center_h = node_size(center)
    result = {str(center["id"]): Rect(area.cx - center_w / 2, area.cy - center_h / 2, center_w, center_h)}
    peers = ordered[1:]
    if not peers:
        return result
    radius_x = max(180.0, area.w * 0.36)
    radius_y = max(140.0, area.h * 0.34)
    for index, node in enumerate(peers):
        angle = -math.pi / 2 + 2 * math.pi * index / len(peers)
        width, height = node_size(node)
        x = area.cx + math.cos(angle) * radius_x - width / 2
        y = area.cy + math.sin(angle) * radius_y - height / 2
        result[str(node["id"])] = Rect(x, y, width, height)
    return result


def _sequence_positions(nodes: list[dict[str, Any]], area: Rect) -> dict[str, Rect]:
    ordered = sorted(nodes, key=_sort_key)
    if not ordered:
        return {}
    slot = area.w / len(ordered)
    result: dict[str, Rect] = {}
    for index, node in enumerate(ordered):
        width, height = node_size(node)
        width = min(width, max(124.0, slot - 28.0))
        width, height = _preserve_presentation_envelope(node, width, height)
        x = area.x + index * slot + (slot - width) / 2
        result[str(node["id"])] = Rect(x, area.y + 12.0, width, height)
    return result


def _nested_positions(
    nodes: list[dict[str, Any]], boundaries: list[dict[str, Any]], area: Rect
) -> tuple[dict[str, Rect], dict[str, Rect]]:
    if not boundaries:
        return _grid_positions(nodes, area), {}
    boundary_by_id = {str(boundary["id"]): boundary for boundary in boundaries}
    children: dict[str | None, list[dict[str, Any]]] = {}
    for boundary in boundaries:
        parent = boundary.get("parent")
        children.setdefault(str(parent) if parent else None, []).append(boundary)
    for values in children.values():
        values.sort(key=_sort_key)

    boundary_rects: dict[str, Rect] = {}
    node_rects: dict[str, Rect] = {}
    top = children.get(None, [])
    top_columns = min(3, max(1, len(top)))
    top_rows = math.ceil(len(top) / top_columns)
    top_gap = 28.0
    top_w = (area.w - top_gap * (top_columns - 1)) / top_columns
    top_h = (area.h - top_gap * (top_rows - 1)) / top_rows
    for index, boundary in enumerate(top):
        row, column = divmod(index, top_columns)
        rect = Rect(area.x + column * (top_w + top_gap), area.y + row * (top_h + top_gap), top_w, top_h)
        boundary_rects[str(boundary["id"])] = rect

    def place_inside(boundary_id: str) -> None:
        rect = boundary_rects[boundary_id]
        direct_nodes = [node for node in nodes if str(node.get("boundary", "")) == boundary_id]
        child_boundaries = children.get(boundary_id, [])
        content = Rect(rect.x + 24.0, rect.y + 54.0, max(120.0, rect.w - 48.0), max(70.0, rect.h - 78.0))
        if child_boundaries:
            node_band_h = min(130.0, content.h * 0.30) if direct_nodes else 0.0
            if direct_nodes:
                node_rects.update(_grid_positions(direct_nodes, Rect(content.x, content.y, content.w, node_band_h), columns=len(direct_nodes)))
            child_y = content.y + node_band_h + (18.0 if direct_nodes else 0.0)
            child_h = max(100.0, content.bottom - child_y)
            child_gap = 20.0
            child_w = (content.w - child_gap * (len(child_boundaries) - 1)) / len(child_boundaries)
            for child_index, child in enumerate(child_boundaries):
                child_id = str(child["id"])
                boundary_rects[child_id] = Rect(content.x + child_index * (child_w + child_gap), child_y, child_w, child_h)
                place_inside(child_id)
        else:
            node_rects.update(_grid_positions(direct_nodes, content))

    for boundary in top:
        place_inside(str(boundary["id"]))

    unbound = [node for node in nodes if not node.get("boundary") or str(node.get("boundary")) not in boundary_by_id]
    if unbound:
        unbound_area = Rect(area.x, max(92.0, area.y - 92.0), area.w, 86.0)
        node_rects.update(_grid_positions(unbound, unbound_area, columns=len(unbound)))
    return node_rects, boundary_rects


def _swimlane_positions(
    nodes: list[dict[str, Any]], boundaries: list[dict[str, Any]], area: Rect
) -> tuple[dict[str, Rect], dict[str, Rect]]:
    if not boundaries:
        return _grid_positions(nodes, area), {}
    ordered_boundaries = sorted(boundaries, key=_sort_key)
    gap = 18.0
    lane_h = (area.h - gap * (len(ordered_boundaries) - 1)) / len(ordered_boundaries)
    boundary_rects: dict[str, Rect] = {}
    node_rects: dict[str, Rect] = {}
    for index, boundary in enumerate(ordered_boundaries):
        boundary_id = str(boundary["id"])
        rect = Rect(area.x, area.y + index * (lane_h + gap), area.w, lane_h)
        boundary_rects[boundary_id] = rect
        lane_nodes = [node for node in nodes if str(node.get("boundary", "")) == boundary_id]
        node_area = Rect(rect.x + 170.0, rect.y + 38.0, max(160.0, rect.w - 194.0), max(58.0, rect.h - 54.0))
        node_rects.update(_grid_positions(lane_nodes, node_area, columns=max(1, len(lane_nodes))))
    unbound = [node for node in nodes if not node.get("boundary")]
    if unbound:
        node_rects.update(_grid_positions(unbound, Rect(area.x, area.y - 88.0, area.w, 78.0), columns=len(unbound)))
    return node_rects, boundary_rects


def _layout_role(item: dict[str, Any]) -> str:
    layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
    return str(layout.get("role", item.get("role", ""))).strip().lower()


def _hub_spoke_positions(model: dict[str, Any], area: Rect) -> tuple[dict[str, Rect], dict[str, Rect]]:
    """Lay out a provider-reference analytical hub with towers, spokes, and a lower enrichment zone."""
    nodes = list(model.get("nodes", []))
    boundaries = list(model.get("boundaries", []))
    foundations = [
        boundary
        for boundary in boundaries
        if str(boundary.get("presentation", boundary.get("kind", ""))).lower()
        in {"foundation-band", "foundation", "platform"}
        and not boundary.get("parent")
    ]
    workload_boundaries = [boundary for boundary in boundaries if boundary not in foundations and not boundary.get("parent")]
    foundation_h = 142.0 if foundations else 0.0
    foundation_gap = 24.0 if foundations else 0.0
    workload = Rect(area.x, area.y, area.w, max(360.0, area.h - foundation_h - foundation_gap))

    role_slots = {
        "source": Rect(workload.x, workload.y + workload.h * 0.05, workload.w * 0.16, workload.h * 0.79),
        "ingest": Rect(workload.x + workload.w * 0.19, workload.y + workload.h * 0.13, workload.w * 0.16, workload.h * 0.58),
        "hub": Rect(workload.x + workload.w * 0.405, workload.y + workload.h * 0.18, workload.w * 0.20, workload.h * 0.48),
        "consumer": Rect(workload.x + workload.w * 0.75, workload.y + workload.h * 0.05, workload.w * 0.22, workload.h * 0.79),
        "satellite": Rect(workload.x + workload.w * 0.33, workload.y + workload.h * 0.73, workload.w * 0.39, workload.h * 0.23),
    }
    aliases = {
        "sources": "source",
        "left": "source",
        "ingress": "ingest",
        "stream-ingest": "ingest",
        "core": "hub",
        "center": "hub",
        "analytical-hub": "hub",
        "consume": "consumer",
        "insights": "consumer",
        "right": "consumer",
        "enrichment": "satellite",
        "advanced-analytics": "satellite",
        "ml": "satellite",
    }
    fallback_roles = ("source", "ingest", "hub", "consumer", "satellite")
    role_groups: dict[str, list[dict[str, Any]]] = {role: [] for role in fallback_roles}
    for index, boundary in enumerate(sorted(workload_boundaries, key=_sort_key)):
        raw_role = _layout_role(boundary)
        role = aliases.get(raw_role, raw_role)
        if role not in role_groups:
            role = fallback_roles[min(index, len(fallback_roles) - 1)]
        role_groups[role].append(boundary)

    boundary_rects: dict[str, Rect] = {}
    for role, items in role_groups.items():
        if not items:
            continue
        slot = role_slots[role]
        gap = 18.0
        if len(items) == 1:
            rects = [slot]
        else:
            item_h = (slot.h - gap * (len(items) - 1)) / len(items)
            rects = [Rect(slot.x, slot.y + i * (item_h + gap), slot.w, item_h) for i in range(len(items))]
        for boundary, rect in zip(items, rects):
            if str(boundary.get("presentation", "")).lower() == "hub-ring":
                side = min(rect.w, rect.h)
                rect = Rect(rect.cx - side / 2.0, rect.cy - side / 2.0, side, side)
            boundary_rects[str(boundary["id"])] = rect

    for index, foundation in enumerate(sorted(foundations, key=_sort_key)):
        band_h = foundation_h / max(1, len(foundations))
        boundary_rects[str(foundation["id"])] = Rect(
            area.x,
            workload.bottom + foundation_gap + index * band_h,
            area.w,
            band_h,
        )

    boundary_by_id = {str(boundary["id"]): boundary for boundary in boundaries}
    node_rects: dict[str, Rect] = {}
    for boundary_id, rect in boundary_rects.items():
        direct_nodes = [node for node in nodes if str(node.get("boundary", "")) == boundary_id]
        if not direct_nodes:
            continue
        boundary = boundary_by_id[boundary_id]
        presentation = str(boundary.get("presentation", boundary.get("kind", ""))).lower()
        role = aliases.get(_layout_role(boundary), _layout_role(boundary))
        if presentation in {"foundation-band", "foundation", "platform"}:
            content = Rect(rect.x + 150.0, rect.y + 14.0, max(160.0, rect.w - 172.0), max(80.0, rect.h - 28.0))
            columns = len(direct_nodes)
        elif presentation == "hub-ring":
            inset = max(46.0, rect.w * 0.18)
            content = Rect(rect.x + inset, rect.y + inset, max(120.0, rect.w - inset * 2), max(100.0, rect.h - inset * 2))
            columns = 1
        else:
            content = Rect(rect.x + 16.0, rect.y + 48.0, max(120.0, rect.w - 32.0), max(90.0, rect.h - 64.0))
            layout = boundary.get("layout") if isinstance(boundary.get("layout"), dict) else {}
            columns = len(direct_nodes) if role == "satellite" or str(layout.get("flow", "")).lower() == "row" else 1
        node_rects.update(_grid_positions(direct_nodes, content, columns=max(1, columns)))

    unbound = [node for node in nodes if str(node.get("boundary", "")) not in boundary_rects]
    if unbound:
        by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in fallback_roles}
        for node in unbound:
            role = aliases.get(_layout_role(node), _layout_role(node))
            by_role[role if role in by_role else "satellite"].append(node)
        for role, role_nodes in by_role.items():
            if not role_nodes:
                continue
            slot = role_slots[role]
            node_rects.update(_grid_positions(role_nodes, slot, columns=len(role_nodes) if role == "satellite" else 1))
    return node_rects, boundary_rects


def _reference_positions(model: dict[str, Any], area: Rect) -> tuple[dict[str, Rect], dict[str, Rect]]:
    """Lay out reference diagrams as weighted columns or rows with optional nested scopes."""
    nodes = list(model.get("nodes", []))
    boundaries = list(model.get("boundaries", []))
    strategy = str(model.get("layoutStrategy", "phase-columns"))
    if strategy == "hub-and-spoke":
        return _hub_spoke_positions(model, area)
    phases = [
        boundary for boundary in boundaries
        if str(boundary.get("presentation", boundary.get("kind", ""))).lower() in {"phase-column", "outline-phase", "phase-row", "phase", "stage"}
        and not boundary.get("parent")
    ]
    phases.sort(key=_sort_key)
    foundations = [
        boundary for boundary in boundaries
        if str(boundary.get("presentation", boundary.get("kind", ""))).lower() in {"foundation-band", "foundation", "platform"}
        and not boundary.get("parent")
    ]
    foundations.sort(key=_sort_key)
    groups = [boundary for boundary in boundaries if boundary.get("parent")]
    groups.sort(key=_sort_key)

    boundary_rects: dict[str, Rect] = {}
    node_rects: dict[str, Rect] = {}
    foundation_h = 142.0 if foundations else 0.0
    foundation_gap = 24.0 if foundations else 0.0
    phase_area = Rect(area.x, area.y, area.w, max(180.0, area.h - foundation_h - foundation_gap))
    gap = 22.0
    total_weight = sum(max(0.25, float(boundary.get("weight", 1.0))) for boundary in phases) or 1.0
    row_mode = strategy == "phase-rows" or any(
        str(phase.get("presentation", "")).lower() == "phase-row" for phase in phases
    )
    if row_mode:
        usable_h = phase_area.h - gap * max(0, len(phases) - 1)
        cursor_y = phase_area.y
        for phase in phases:
            phase_id = str(phase["id"])
            weight = max(0.25, float(phase.get("weight", 1.0)))
            phase_h = usable_h * weight / total_weight
            boundary_rects[phase_id] = Rect(phase_area.x, cursor_y, phase_area.w, phase_h)
            cursor_y += phase_h + gap
    else:
        usable_w = phase_area.w - gap * max(0, len(phases) - 1)
        cursor_x = phase_area.x
        for phase in phases:
            phase_id = str(phase["id"])
            weight = max(0.25, float(phase.get("weight", 1.0)))
            phase_w = usable_w * weight / total_weight
            boundary_rects[phase_id] = Rect(cursor_x, phase_area.y, phase_w, phase_area.h)
            cursor_x += phase_w + gap

    for index, foundation in enumerate(foundations):
        foundation_id = str(foundation["id"])
        band_h = foundation_h / max(1, len(foundations))
        boundary_rects[foundation_id] = Rect(
            area.x,
            phase_area.bottom + foundation_gap + index * band_h,
            area.w,
            band_h,
        )

    for group in groups:
        parent_id = str(group.get("parent", ""))
        parent_rect = boundary_rects.get(parent_id)
        if not parent_rect:
            continue
        override = group.get("layout") if isinstance(group.get("layout"), dict) else {}
        gx = float(override.get("x", 0.08))
        gy = float(override.get("y", 0.48))
        gw = float(override.get("width", 0.84))
        gh = float(override.get("height", 0.43))
        boundary_rects[str(group["id"])] = Rect(
            parent_rect.x + parent_rect.w * gx,
            parent_rect.y + parent_rect.h * gy,
            parent_rect.w * gw,
            parent_rect.h * gh,
        )

    boundary_by_id = {str(boundary["id"]): boundary for boundary in boundaries}
    for boundary_id, rect in boundary_rects.items():
        direct_nodes = [node for node in nodes if str(node.get("boundary", "")) == boundary_id]
        if not direct_nodes:
            continue
        boundary = boundary_by_id.get(boundary_id, {})
        presentation = str(boundary.get("presentation", boundary.get("kind", ""))).lower()
        if presentation in {"foundation-band", "foundation", "platform"}:
            content = Rect(rect.x + 150.0, rect.y + 16.0, max(160.0, rect.w - 172.0), max(80.0, rect.h - 30.0))
            slot = content.w / len(direct_nodes)
            for index, node in enumerate(sorted(direct_nodes, key=_sort_key)):
                desired_w, desired_h = node_size(node)
                width = min(desired_w, max(104.0, slot - 16.0))
                height = min(desired_h, content.h)
                width, height = _preserve_presentation_envelope(node, width, height)
                node_rects[str(node["id"])] = Rect(
                    content.x + index * slot + (slot - width) / 2,
                    content.y + (content.h - height) / 2,
                    width,
                    height,
                )
        else:
            boundary_layout = boundary.get("layout") if isinstance(boundary.get("layout"), dict) else {}
            horizontal = row_mode and not boundary.get("parent") or str(boundary_layout.get("flow", "")).lower() == "row"
            if horizontal:
                label_gutter = 142.0 if presentation == "phase-row" or row_mode and not boundary.get("parent") else 10.0
                content = Rect(rect.x + label_gutter, rect.y + 10.0, max(120.0, rect.w - label_gutter - 14.0), max(72.0, rect.h - 20.0))
            else:
                header = 44.0 if boundary.get("parent") else 54.0
                content = Rect(rect.x + 10.0, rect.y + header, max(100.0, rect.w - 20.0), max(96.0, rect.h - header - 16.0))
            ordered = sorted(direct_nodes, key=_sort_key)
            slot = (content.w if horizontal else content.h) / len(ordered)
            for index, node in enumerate(ordered):
                desired_w, desired_h = node_size(node)
                node_layout = node.get("layout") if isinstance(node.get("layout"), dict) else {}
                track_value = node_layout.get("track")
                cross_track_value = node_layout.get("crossTrack")
                try:
                    track = max(0.0, min(1.0, float(track_value))) if track_value is not None else None
                except (TypeError, ValueError):
                    track = None
                try:
                    cross_track = max(0.0, min(1.0, float(cross_track_value))) if cross_track_value is not None else None
                except (TypeError, ValueError):
                    cross_track = None
                if horizontal:
                    width = min(desired_w, max(96.0, slot - 14.0))
                    height = min(desired_h, max(64.0, content.h - 8.0))
                    width, height = _preserve_presentation_envelope(node, width, height)
                    center_x = content.x + content.w * track if track is not None else content.x + index * slot + slot / 2
                    node_rects[str(node["id"])] = Rect(
                        max(content.x, min(center_x - width / 2, content.right - width)),
                        max(content.y, min(content.y + content.h * cross_track - height / 2, content.bottom - height)) if cross_track is not None else content.y + (content.h - height) / 2,
                        width,
                        height,
                    )
                else:
                    width = min(desired_w, max(96.0, content.w - 8.0))
                    height = min(desired_h, max(70.0, slot - 14.0))
                    width, height = _preserve_presentation_envelope(node, width, height)
                    center_y = content.y + content.h * track if track is not None else content.y + index * slot + slot / 2
                    node_rects[str(node["id"])] = Rect(
                        content.x + (content.w - width) / 2,
                        max(content.y, min(center_y - height / 2, content.bottom - height)),
                        width,
                        height,
                    )

    unbound = [node for node in nodes if str(node.get("boundary", "")) not in boundary_rects]
    if unbound:
        node_rects.update(_grid_positions(unbound, phase_area, columns=max(1, len(unbound))))
    return node_rects, boundary_rects


def _derived_boundary_rects(
    nodes: dict[str, Rect], model_nodes: list[dict[str, Any]], boundaries: list[dict[str, Any]]
) -> dict[str, Rect]:
    by_parent: dict[str, list[Rect]] = {}
    for node in model_nodes:
        boundary_id = node.get("boundary")
        node_rect = nodes.get(str(node.get("id")))
        if boundary_id and node_rect:
            by_parent.setdefault(str(boundary_id), []).append(node_rect)
    result: dict[str, Rect] = {}
    pending = list(sorted(boundaries, key=lambda item: (str(item.get("parent", "")).count("/"), *_sort_key(item)), reverse=True))
    for boundary in pending:
        boundary_id = str(boundary["id"])
        members = list(by_parent.get(boundary_id, []))
        members.extend(rect for child_id, rect in result.items() if str(next((b.get("parent") for b in boundaries if str(b.get("id")) == child_id), "")) == boundary_id)
        if members:
            left = min(rect.left for rect in members) - 28.0
            right = max(rect.right for rect in members) + 28.0
            top = min(rect.top for rect in members) - 54.0
            bottom = max(rect.bottom for rect in members) + 26.0
            result[boundary_id] = Rect(left, top, right - left, bottom - top)
    return result


def _edge_route(
    source: Rect,
    target: Rect,
    direction: str,
    sequence_y: float | None = None,
    edge_layout: dict[str, Any] | None = None,
) -> EdgeRoute:
    edge_layout = edge_layout or {}
    if sequence_y is not None:
        start_y = source.bottom + 18.0
        target_y = target.bottom + 18.0
        points = ((source.cx, start_y), (source.cx, sequence_y), (target.cx, sequence_y), (target.cx, target_y))
        return EdgeRoute(points, 0.5, 1.0, 0.5, 1.0)
    if edge_layout.get("sourcePort") is not None or edge_layout.get("targetPort") is not None:
        source_point, exit_x, exit_y = _explicit_port_attachment(
            source,
            edge_layout.get("sourcePort"),
            str(edge_layout.get("sourceSide", "right")),
        )
        target_point, entry_x, entry_y = _explicit_port_attachment(
            target,
            edge_layout.get("targetPort"),
            str(edge_layout.get("targetSide", "left")),
        )

        def outward(x: float, y: float) -> tuple[float, float]:
            if x == 0.0:
                return (-1.0, 0.0)
            if x == 1.0:
                return (1.0, 0.0)
            if y == 0.0:
                return (0.0, -1.0)
            return (0.0, 1.0)

        source_normal = outward(exit_x, exit_y)
        target_normal = outward(entry_x, entry_y)
        source_stub = (source_point[0] + source_normal[0] * 24.0, source_point[1] + source_normal[1] * 24.0)
        target_stub = (target_point[0] + target_normal[0] * 24.0, target_point[1] + target_normal[1] * 24.0)
        source_horizontal = source_normal[0] != 0.0
        target_horizontal = target_normal[0] != 0.0
        if source_horizontal and target_horizontal:
            try:
                mid_x = float(edge_layout.get("midX", (source_stub[0] + target_stub[0]) / 2.0))
            except (TypeError, ValueError):
                mid_x = (source_stub[0] + target_stub[0]) / 2.0
            points = (source_stub, (mid_x, source_stub[1]), (mid_x, target_stub[1]), target_stub)
        elif not source_horizontal and not target_horizontal:
            try:
                mid_y = float(edge_layout.get("midY", (source_stub[1] + target_stub[1]) / 2.0))
            except (TypeError, ValueError):
                mid_y = (source_stub[1] + target_stub[1]) / 2.0
            points = (source_stub, (source_stub[0], mid_y), (target_stub[0], mid_y), target_stub)
        elif source_horizontal:
            points = (source_stub, (target_stub[0], source_stub[1]), target_stub)
        else:
            points = (source_stub, (source_stub[0], target_stub[1]), target_stub)
        return EdgeRoute(points, exit_x, exit_y, entry_x, entry_y)
    horizontal = direction in {"LR", "RL"} and abs(target.cx - source.cx) > max(source.w, target.w) * 0.55
    if horizontal:
        left_to_right = target.cx >= source.cx
        sx = source.right + 24.0 if left_to_right else source.left - 24.0
        tx = target.left - 24.0 if left_to_right else target.right + 24.0
        if abs(target.cy - source.cy) <= 3.0:
            return EdgeRoute(
                ((sx, source.cy), (tx, target.cy)),
                1.0 if left_to_right else 0.0,
                0.5,
                0.0 if left_to_right else 1.0,
                0.5,
            )
        try:
            mid_x = float(edge_layout.get("midX", (sx + tx) / 2.0))
        except (TypeError, ValueError):
            mid_x = (sx + tx) / 2.0
        points = ((sx, source.cy), (mid_x, source.cy), (mid_x, target.cy), (tx, target.cy))
        return EdgeRoute(points, 1.0 if left_to_right else 0.0, 0.5, 0.0 if left_to_right else 1.0, 0.5)
    top_to_bottom = target.cy >= source.cy
    sy = source.bottom + 24.0 if top_to_bottom else source.top - 24.0
    ty = target.top - 24.0 if top_to_bottom else target.bottom + 24.0
    try:
        mid_y = float(edge_layout.get("midY", (sy + ty) / 2.0))
    except (TypeError, ValueError):
        mid_y = (sy + ty) / 2.0
    points = ((source.cx, sy), (source.cx, mid_y), (target.cx, mid_y), (target.cx, ty))
    return EdgeRoute(points, 0.5, 1.0 if top_to_bottom else 0.0, 0.5, 0.0 if top_to_bottom else 1.0)


def _return_route(source: Rect, target: Rect, lane: Rect) -> EdgeRoute:
    route_y = max(lane.top + 54.0, min(source.top, target.top) - 52.0)
    points = (
        (source.cx, source.top - 18.0),
        (source.cx, route_y),
        (target.cx, route_y),
        (target.cx, target.top - 18.0),
    )
    return EdgeRoute(points, 0.5, 0.0, 0.5, 0.0)


def _rail_route(
    source: Rect,
    target: Rect,
    rail: str | float,
    content: Rect,
    workload_bottom: float,
    edge_layout: dict[str, Any],
) -> EdgeRoute:
    try:
        lane = max(0, int(edge_layout.get("lane", 0)))
    except (TypeError, ValueError):
        lane = 0
    try:
        lane_spacing = max(24.0, float(edge_layout.get("laneSpacing", 36.0)))
    except (TypeError, ValueError):
        lane_spacing = 36.0
    try:
        rail_y = float(rail)
        use_top = rail_y <= (source.cy + target.cy) / 2.0
    except (TypeError, ValueError):
        use_top = str(rail).lower() == "top"
        rail_y = content.top + 66.0 + lane * lane_spacing if use_top else workload_bottom - 28.0 - lane * lane_spacing
    left_to_right = target.cx >= source.cx
    source_side = str(edge_layout.get("sourceSide", "right" if left_to_right else "left")).lower()
    target_side = str(edge_layout.get("targetSide", "left" if left_to_right else "right")).lower()
    source_point, exit_x, exit_y = _explicit_port_attachment(source, edge_layout.get("sourcePort"), source_side)
    target_point, entry_x, entry_y = _explicit_port_attachment(target, edge_layout.get("targetPort"), target_side)
    source_right = exit_x != 0.0
    target_right = entry_x == 1.0
    source_x = source_point[0] + (18.0 if source_right else -18.0)
    try:
        source_lane = max(0, int(edge_layout.get("sourceLane", 0)))
    except (TypeError, ValueError):
        source_lane = 0
    try:
        target_lane = max(0, int(edge_layout.get("targetLane", 0)))
    except (TypeError, ValueError):
        target_lane = 0
    source_gutter_offset = 34.0 + source_lane * lane_spacing
    target_gutter_offset = 34.0 + target_lane * lane_spacing
    source_gutter = source.right + source_gutter_offset if source_right else source.left - source_gutter_offset
    target_gutter = target.right + target_gutter_offset if target_right else target.left - target_gutter_offset
    target_x = target_point[0] + (18.0 if target_right else -18.0)
    points = (
        (source_x, source_point[1]),
        (source_gutter, source_point[1]),
        (source_gutter, rail_y),
        (target_gutter, rail_y),
        (target_gutter, target_point[1]),
        (target_x, target_point[1]),
    )
    return EdgeRoute(points, exit_x, exit_y, entry_x, entry_y)


def _side_gutter_route(source: Rect, target: Rect, side: str, content: Rect, edge_layout: dict[str, Any]) -> EdgeRoute:
    right_side = str(side).lower() != "left"
    try:
        lane = max(0, int(edge_layout.get("lane", 0)))
    except (TypeError, ValueError):
        lane = 0
    try:
        lane_spacing = max(24.0, float(edge_layout.get("laneSpacing", 36.0)))
    except (TypeError, ValueError):
        lane_spacing = 36.0
    gutter_x = content.right - 8.0 - lane * lane_spacing if right_side else content.left + 8.0 + lane * lane_spacing
    source_x = source.right + 18.0 if right_side else source.left - 18.0
    target_x = target.right + 18.0 if right_side else target.left - 18.0
    points = ((source_x, source.cy), (gutter_x, source.cy), (gutter_x, target.cy), (target_x, target.cy))
    side_port = 1.0 if right_side else 0.0
    return EdgeRoute(points, side_port, 0.5, side_port, 0.5)


def _cross_lane_route(source: Rect, target: Rect, source_lane: Rect, content: Rect) -> EdgeRoute:
    route_y = source_lane.bottom - 50.0
    gutter_x = content.right - 18.0
    target_from_right = target.right + 18.0
    points = (
        (source.cx, source.bottom + 18.0),
        (source.cx, route_y),
        (gutter_x, route_y),
        (gutter_x, target.cy),
        (target_from_right, target.cy),
    )
    return EdgeRoute(points, 0.5, 1.0, 1.0, 0.5)


def _side_attachment(rect: Rect, side: str) -> tuple[tuple[float, float], float, float]:
    normalized = str(side).lower()
    if normalized == "left":
        return (rect.left, rect.cy), 0.0, 0.5
    if normalized == "top":
        return (rect.cx, rect.top), 0.5, 0.0
    if normalized == "bottom":
        return (rect.cx, rect.bottom), 0.5, 1.0
    return (rect.right, rect.cy), 1.0, 0.5


def _explicit_port_attachment(
    rect: Rect, value: Any, fallback_side: str
) -> tuple[tuple[float, float], float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            x = max(0.0, min(1.0, float(value[0])))
            y = max(0.0, min(1.0, float(value[1])))
        except (TypeError, ValueError):
            return _side_attachment(rect, fallback_side)
        if x in {0.0, 1.0} or y in {0.0, 1.0}:
            return (rect.left + rect.w * x, rect.top + rect.h * y), x, y
    return _side_attachment(rect, fallback_side)


def _custom_route(source: Rect, target: Rect, edge_layout: dict[str, Any]) -> EdgeRoute:
    source_point, exit_x, exit_y = _explicit_port_attachment(
        source,
        edge_layout.get("sourcePort"),
        str(edge_layout.get("sourceSide", "right")),
    )
    target_point, entry_x, entry_y = _explicit_port_attachment(
        target,
        edge_layout.get("targetPort"),
        str(edge_layout.get("targetSide", "left")),
    )
    waypoints: list[tuple[float, float]] = []
    for value in edge_layout.get("waypoints", []):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            continue
        try:
            waypoints.append((float(value[0]), float(value[1])))
        except (TypeError, ValueError):
            continue
    return EdgeRoute((source_point, *waypoints, target_point), exit_x, exit_y, entry_x, entry_y)


def layout_model(model: dict[str, Any], adapter: str) -> LayoutResult:
    canvas = model["canvas"]
    width = float(canvas["width"])
    height = float(canvas["height"])
    show_title = bool(model.get("showTitle", True))
    content = Rect(58.0, 118.0 if show_title else 54.0, width - 116.0, height - (208.0 if show_title else 96.0))
    nodes = list(model.get("nodes", []))
    boundaries = list(model.get("boundaries", []))
    boundary_rects: dict[str, Rect] = {}

    if adapter in {"nested"}:
        node_rects, boundary_rects = _nested_positions(nodes, boundaries, content)
    elif adapter in {"swimlane", "rag"}:
        node_rects, boundary_rects = _swimlane_positions(nodes, boundaries, content)
    elif adapter == "reference":
        node_rects, boundary_rects = _reference_positions(model, content)
    elif adapter == "radial":
        node_rects = _radial_positions(nodes, content)
    elif adapter == "sequence":
        node_rects = _sequence_positions(nodes, content)
    elif adapter == "layered":
        node_rects = _layered_positions(model, content)
    elif adapter == "tree":
        node_rects = _layered_positions(model, content, tree=True)
    elif adapter in {"grid", "erd", "matrix"}:
        columns = 2 if adapter in {"erd", "matrix"} else None
        node_rects = _grid_positions(nodes, content, columns=columns)
    else:
        raise ValueError(f"Unsupported layout adapter: {adapter}")

    if boundaries and not boundary_rects:
        boundary_rects = _derived_boundary_rects(node_rects, nodes, boundaries)

    direction = "TB" if adapter == "tree" else str(model.get("direction", "LR"))
    edge_routes: dict[str, EdgeRoute] = {}
    ordered_edges = sorted(model.get("edges", []), key=_sort_key)
    model_nodes = {str(node["id"]): node for node in nodes}
    workload_rects = [
        rect for boundary_id, rect in boundary_rects.items()
        if str(next((item.get("presentation", item.get("kind", "")) for item in boundaries if str(item.get("id")) == boundary_id), "")).lower()
        not in {"foundation-band", "foundation", "platform"}
    ]
    workload_bottom = max((rect.bottom for rect in workload_rects), default=content.bottom)
    for index, edge in enumerate(ordered_edges):
        source = node_rects.get(str(edge.get("source")))
        target = node_rects.get(str(edge.get("target")))
        if not source or not target:
            continue
        event_y = 272.0 + index * 54.0 if adapter == "sequence" else None
        source_boundary = str(model_nodes.get(str(edge.get("source")), {}).get("boundary", ""))
        target_boundary = str(model_nodes.get(str(edge.get("target")), {}).get("boundary", ""))
        edge_kind = str(edge.get("kind", "")).lower()
        edge_layout = edge.get("layout") if isinstance(edge.get("layout"), dict) else {}
        if edge_layout.get("waypoints"):
            edge_routes[str(edge["id"])] = _custom_route(source, target, edge_layout)
        elif adapter == "reference" and edge_layout.get("rail") is not None:
            edge_routes[str(edge["id"])] = _rail_route(source, target, edge_layout["rail"], content, workload_bottom, edge_layout)
        elif adapter == "reference" and edge_layout.get("gutter") is not None:
            edge_routes[str(edge["id"])] = _side_gutter_route(source, target, str(edge_layout["gutter"]), content, edge_layout)
        elif adapter in {"rag", "swimlane"} and source_boundary and target_boundary and source_boundary != target_boundary:
            source_lane = boundary_rects.get(source_boundary, content)
            edge_routes[str(edge["id"])] = _cross_lane_route(source, target, source_lane, content)
        elif adapter in {"rag", "swimlane"} and edge_kind in {"response", "feedback", "return"}:
            edge_routes[str(edge["id"])] = _return_route(source, target, boundary_rects.get(source_boundary, content))
        else:
            edge_routes[str(edge["id"])] = _edge_route(source, target, direction, event_y, edge_layout)

    return LayoutResult(node_rects, boundary_rects, edge_routes, adapter)
