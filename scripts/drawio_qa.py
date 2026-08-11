#!/usr/bin/env python3
"""Lightweight QA checks for draw.io mxGraphModel files.

Uses only Python standard library. It catches common presentation-quality issues:
invalid XML, overlapping boxes, connector segments crossing unrelated boxes,
misconfigured relationship labels, and likely service labels rendered as plain
boxes instead of icon/library shapes.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Iterable


ICON_KEYWORDS = [
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "kubernetes",
    "docker",
    "rancher",
    "grafana",
    "prometheus",
    "power bi",
    "superset",
    "s3",
    "queue",
    "postgres",
    "postgresql",
    "redis",
    "snowflake",
    "databricks",
    "sharepoint",
    "service bus",
    "cosmos",
    "cosmosdb",
]

ICON_STYLE_HINTS = ["shape=mxgraph.", "shape=image", "image;", "image=", "sketch=0;"]

@dataclass(frozen=True)
class Box:
    cell_id: str
    parent_id: str | None
    label: str
    x: float
    y: float
    w: float
    h: float
    style: str
    tags: frozenset[str]

    @property
    def is_container(self) -> bool:
        return "container=1" in self.style.lower() or "swimlane" in self.style.lower()

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
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)


@dataclass(frozen=True)
class Edge:
    cell_id: str
    source: str | None
    target: str | None
    points: list[tuple[float, float]]
    style: str
    label: str
    label_offset_y: float
    tags: frozenset[str]


def clean_label(value: str | None) -> str:
    if not value:
        return ""
    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_float(value: str | None, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def parse_style(style: str) -> dict[str, str]:
    properties: dict[str, str] = {}
    for token in style.split(";"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        properties[key] = value
    return properties


def parse_tags(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    return frozenset(token for token in re.split(r"[\s,]+", value.strip()) if token)


def load_cells(path: Path) -> tuple[list[Box], list[Edge], float, float]:
    tree = ET.parse(path)
    root = tree.getroot()
    page_width = parse_float(root.attrib.get("pageWidth"))
    page_height = parse_float(root.attrib.get("pageHeight"))
    boxes: list[Box] = []
    edges: list[Edge] = []

    cells_by_id = {cell.attrib.get("id", ""): cell for cell in root.iter("mxCell")}
    absolute_origins: dict[str, tuple[float, float]] = {}

    def absolute_origin(cell_id: str, visiting: set[str] | None = None) -> tuple[float, float]:
        if cell_id in absolute_origins:
            return absolute_origins[cell_id]
        cell = cells_by_id.get(cell_id)
        if cell is None:
            return (0.0, 0.0)
        visiting = visiting or set()
        if cell_id in visiting:
            return (0.0, 0.0)
        visiting.add(cell_id)
        geom = cell.find("mxGeometry")
        local_x = parse_float(geom.attrib.get("x")) if geom is not None else 0.0
        local_y = parse_float(geom.attrib.get("y")) if geom is not None else 0.0
        parent_id = cell.attrib.get("parent")
        parent_x, parent_y = absolute_origin(parent_id, visiting) if parent_id else (0.0, 0.0)
        origin = (parent_x + local_x, parent_y + local_y)
        absolute_origins[cell_id] = origin
        visiting.remove(cell_id)
        return origin

    for cell in root.iter("mxCell"):
        cell_id = cell.attrib.get("id", "")
        style = cell.attrib.get("style", "")
        geom = cell.find("mxGeometry")

        if cell.attrib.get("vertex") == "1" and geom is not None:
            absolute_x, absolute_y = absolute_origin(cell_id)
            boxes.append(
                Box(
                    cell_id=cell_id,
                    parent_id=cell.attrib.get("parent"),
                    label=clean_label(cell.attrib.get("value")),
                    x=absolute_x,
                    y=absolute_y,
                    w=parse_float(geom.attrib.get("width")),
                    h=parse_float(geom.attrib.get("height")),
                    style=style,
                    tags=parse_tags(cell.attrib.get("tags")),
                )
            )

        if cell.attrib.get("edge") == "1":
            points: list[tuple[float, float]] = []
            if geom is not None:
                parent_id = cell.attrib.get("parent")
                parent_x, parent_y = absolute_origin(parent_id) if parent_id else (0.0, 0.0)
                waypoint_nodes = geom.findall("./Array[@as='points']/mxPoint")
                if not waypoint_nodes:
                    waypoint_nodes = [
                        point
                        for point in geom.findall("mxPoint")
                        if point.attrib.get("as") not in {"sourcePoint", "targetPoint"}
                    ]
                for point in waypoint_nodes:
                    points.append(
                        (
                            parent_x + parse_float(point.attrib.get("x")),
                            parent_y + parse_float(point.attrib.get("y")),
                        )
                    )
            edges.append(
                Edge(
                    cell_id=cell_id,
                    source=cell.attrib.get("source"),
                    target=cell.attrib.get("target"),
                    points=points,
                    style=style,
                    label=clean_label(cell.attrib.get("value")),
                    label_offset_y=parse_float(geom.attrib.get("y")) if geom is not None else 0.0,
                    tags=parse_tags(cell.attrib.get("tags")),
                )
            )

    return boxes, edges, page_width, page_height


def boxes_overlap(a: Box, b: Box, padding: float) -> bool:
    return not (
        a.right + padding <= b.left
        or b.right + padding <= a.left
        or a.bottom + padding <= b.top
        or b.bottom + padding <= a.top
    )


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])


def on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return min(a[0], c[0]) <= b[0] <= max(a[0], c[0]) and min(a[1], c[1]) <= b[1] <= max(a[1], c[1])


def segments_intersect(
    p1: tuple[float, float], q1: tuple[float, float], p2: tuple[float, float], q2: tuple[float, float]
) -> bool:
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if o1 * o2 < 0 and o3 * o4 < 0:
        return True

    eps = 1e-9
    if math.isclose(o1, 0.0, abs_tol=eps) and on_segment(p1, p2, q1):
        return True
    if math.isclose(o2, 0.0, abs_tol=eps) and on_segment(p1, q2, q1):
        return True
    if math.isclose(o3, 0.0, abs_tol=eps) and on_segment(p2, p1, q2):
        return True
    if math.isclose(o4, 0.0, abs_tol=eps) and on_segment(p2, q1, q2):
        return True
    return False


def segment_intersects_rect(p1: tuple[float, float], p2: tuple[float, float], box: Box, padding: float) -> bool:
    left = box.left - padding
    right = box.right + padding
    top = box.top - padding
    bottom = box.bottom + padding
    x1, y1 = p1
    x2, y2 = p2

    if max(x1, x2) < left or min(x1, x2) > right or max(y1, y2) < top or min(y1, y2) > bottom:
        return False
    if left <= x1 <= right and top <= y1 <= bottom:
        return True
    if left <= x2 <= right and top <= y2 <= bottom:
        return True

    rect_segments = [
        ((left, top), (right, top)),
        ((right, top), (right, bottom)),
        ((right, bottom), (left, bottom)),
        ((left, bottom), (left, top)),
    ]
    return any(segments_intersect(p1, p2, a, b) for a, b in rect_segments)


def edge_polyline(edge: Edge, boxes_by_id: dict[str, Box]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if edge.source and edge.source in boxes_by_id:
        points.append(boxes_by_id[edge.source].center)
    points.extend(edge.points)
    if edge.target and edge.target in boxes_by_id:
        points.append(boxes_by_id[edge.target].center)
    return points


def manhattan_length(points: list[tuple[float, float]]) -> float:
    return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in pairwise(points))


def bend_count(points: list[tuple[float, float]]) -> int:
    bends = 0
    previous_axis: str | None = None
    for a, b in pairwise(points):
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        if math.isclose(dx, 0.0, abs_tol=1e-9) and math.isclose(dy, 0.0, abs_tol=1e-9):
            continue
        if math.isclose(dy, 0.0, abs_tol=1e-9):
            axis = "horizontal"
        elif math.isclose(dx, 0.0, abs_tol=1e-9):
            axis = "vertical"
        else:
            axis = "diagonal"
        if previous_axis is not None and axis != previous_axis:
            bends += 1
        previous_axis = axis
    return bends


def terminal_entry_issue(edge: Edge, target: Box) -> str | None:
    if not edge.points:
        return None
    style = parse_style(edge.style)
    if "entryX" not in style or "entryY" not in style:
        return None
    entry_x = parse_float(style.get("entryX"), 0.5)
    entry_y = parse_float(style.get("entryY"), 0.5)
    anchor_x, anchor_y = edge.points[-1]
    target_x = target.left + entry_x * target.w
    target_y = target.top + entry_y * target.h
    alignment_tolerance = 4.0
    outside_clearance = 10.0

    enters_left_or_right = entry_x in {0.0, 1.0} and entry_y not in {0.0, 1.0}
    enters_top_or_bottom = entry_y in {0.0, 1.0} and entry_x not in {0.0, 1.0}

    if enters_left_or_right:
        aligned = abs(anchor_y - target_y) <= alignment_tolerance
        outside = anchor_x <= target.left - outside_clearance if entry_x == 0.0 else anchor_x >= target.right + outside_clearance
        if not aligned or not outside:
            side = "left" if entry_x == 0.0 else "right"
            return f"final waypoint {edge.points[-1]} must align horizontally outside the target's {side} port near ({target_x:.1f}, {target_y:.1f})"

    if enters_top_or_bottom:
        aligned = abs(anchor_x - target_x) <= alignment_tolerance
        outside = anchor_y <= target.top - outside_clearance if entry_y == 0.0 else anchor_y >= target.bottom + outside_clearance
        if not aligned or not outside:
            side = "top" if entry_y == 0.0 else "bottom"
            return f"final waypoint {edge.points[-1]} must align vertically outside the target's {side} port near ({target_x:.1f}, {target_y:.1f})"

    return None


def initial_exit_issue(edge: Edge, source: Box) -> str | None:
    if not edge.points:
        return None
    style = parse_style(edge.style)
    if "exitX" not in style or "exitY" not in style:
        return None
    exit_x = parse_float(style.get("exitX"), 0.5)
    exit_y = parse_float(style.get("exitY"), 0.5)
    anchor_x, anchor_y = edge.points[0]
    source_x = source.left + exit_x * source.w
    source_y = source.top + exit_y * source.h
    alignment_tolerance = 4.0
    outside_clearance = 10.0

    leaves_left_or_right = exit_x in {0.0, 1.0} and exit_y not in {0.0, 1.0}
    leaves_top_or_bottom = exit_y in {0.0, 1.0} and exit_x not in {0.0, 1.0}

    if leaves_left_or_right:
        aligned = abs(anchor_y - source_y) <= alignment_tolerance
        outside = anchor_x <= source.left - outside_clearance if exit_x == 0.0 else anchor_x >= source.right + outside_clearance
        if not aligned or not outside:
            side = "left" if exit_x == 0.0 else "right"
            return f"first waypoint {edge.points[0]} must align horizontally outside the source's {side} port near ({source_x:.1f}, {source_y:.1f})"

    if leaves_top_or_bottom:
        aligned = abs(anchor_x - source_x) <= alignment_tolerance
        outside = anchor_y <= source.top - outside_clearance if exit_y == 0.0 else anchor_y >= source.bottom + outside_clearance
        if not aligned or not outside:
            side = "top" if exit_y == 0.0 else "bottom"
            return f"first waypoint {edge.points[0]} must align vertically outside the source's {side} port near ({source_x:.1f}, {source_y:.1f})"

    return None


def is_step_badge(box: Box) -> bool:
    return (
        re.fullmatch(r"(?:[A-Za-z]\d+|\d+[A-Za-z]?)", box.label) is not None
        and box.w <= 44
        and box.h <= 44
        and abs(box.w - box.h) <= 6
        and "ellipse" in box.style.lower()
    )


def pairwise(points: list[tuple[float, float]]) -> Iterable[tuple[tuple[float, float], tuple[float, float]]]:
    for index in range(len(points) - 1):
        yield points[index], points[index + 1]


def maybe_plain_icon_box(box: Box) -> bool:
    if box.is_container or is_step_badge(box) or "qa-icon-exempt" in box.tags:
        return False
    text = box.label.lower()
    if not any(keyword in text for keyword in ICON_KEYWORDS):
        return False
    style = box.style.lower()
    return not any(hint in style for hint in ICON_STYLE_HINTS)


def interval_union_length(intervals: list[tuple[float, float]]) -> float:
    if not intervals:
        return 0.0
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def run_checks(path: Path, padding: float, diagram_type: str = "general") -> tuple[list[str], list[str]]:
    boxes, edges, page_width, page_height = load_cells(path)
    boxes_by_id = {box.cell_id: box for box in boxes}
    errors: list[str] = []
    warnings: list[str] = []

    if diagram_type not in {"general", "overview", "detailed"}:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")

    if boxes and (page_width <= 0 or page_height <= 0):
        left = min(box.left for box in boxes)
        top = min(box.top for box in boxes)
        page_width = max(box.right for box in boxes) - left
        page_height = max(box.bottom for box in boxes) - top

    if diagram_type in {"overview", "detailed"} and page_width > 0 and page_height > 0:
        page_area = page_width * page_height
        support_boxes = [box for box in boxes if "qa-support" in box.tags]
        support_ratio = sum(box.w * box.h for box in support_boxes) / page_area
        if support_ratio > 0.25:
            warnings.append(
                f"Tagged support regions occupy {support_ratio:.1%} of the canvas; keep support at or below 25% so primary content remains dominant."
            )

        chrome_boxes = [
            box for box in boxes if "qa-metadata" in box.tags or "qa-legend" in box.tags
        ]
        chrome_height = interval_union_length([(box.top, box.bottom) for box in chrome_boxes])
        if chrome_height / page_height > 0.12:
            warnings.append(
                f"Tagged metadata and legend bands occupy {chrome_height / page_height:.1%} of canvas height; keep them at or below 12%."
            )

        primary_boxes = [box for box in boxes if "qa-primary" in box.tags]
        if primary_boxes:
            primary_width = max(box.right for box in primary_boxes) - min(box.left for box in primary_boxes)
            if primary_width / page_width < 0.70:
                warnings.append(
                    f"Tagged primary content spans only {primary_width / page_width:.1%} of canvas width; target at least 70% or reduce the canvas."
                )

    def is_ancestor(ancestor_id: str, descendant: Box) -> bool:
        parent_id = descendant.parent_id
        visited: set[str] = set()
        while parent_id and parent_id not in visited:
            if parent_id == ancestor_id:
                return True
            visited.add(parent_id)
            parent_box = boxes_by_id.get(parent_id)
            parent_id = parent_box.parent_id if parent_box else None
        return False

    if diagram_type == "detailed" and page_width > 0:
        for rail in (box for box in boxes if "qa-title-rail" in box.tags):
            if rail.w / page_width > 0.12:
                warnings.append(
                    f"Title rail {rail.cell_id} occupies {rail.w / page_width:.1%} of canvas width; keep a Detailed Request layer rail at or below 12%."
                )

    for index, box in enumerate(boxes):
        if "qa-background" in box.tags:
            continue
        if box.w <= 0 or box.h <= 0:
            warnings.append(f"Box {box.cell_id} '{box.label}' has non-positive size.")
        if maybe_plain_icon_box(box):
            warnings.append(f"Box {box.cell_id} '{box.label}' looks like a real service/component but does not use an image/mxgraph icon style.")
        if (
            not box.is_container
            and box.w * box.h >= 70000
            and len(box.label) < 60
            and "shape=image" not in box.style.lower()
            and "shape=actor" not in box.style.lower()
        ):
            warnings.append(
                f"Box {box.cell_id} '{box.label}' is large for its content density; compact it or use the space for meaningful nested detail."
            )
        has_children = any(other.parent_id == box.cell_id for other in boxes)
        style_lower = box.style.lower()
        if (
            diagram_type in {"overview", "detailed"}
            and not box.is_container
            and not has_children
            and box.w * box.h >= 40000
            and 0 < len(box.label) < 100
            and "qa-density-exempt" not in box.tags
            and not style_lower.startswith("text;")
            and "shape=image" not in style_lower
            and "shape=actor" not in style_lower
        ):
            warnings.append(
                f"Box {box.cell_id} '{box.label}' is a sparse leaf card ({box.w * box.h:.0f}px^2 for {len(box.label)} visible characters); compact it or add meaningful nested detail."
            )
        for other in boxes[index + 1 :]:
            if "qa-background" in other.tags:
                continue
            shared_parent = boxes_by_id.get(box.parent_id or "") if box.parent_id == other.parent_id else None
            if shared_parent and "qa-illustrative" in shared_parent.tags:
                continue
            if (box.is_container and is_ancestor(box.cell_id, other)) or (other.is_container and is_ancestor(other.cell_id, box)):
                continue
            if boxes_overlap(box, other, padding):
                errors.append(f"Overlap: {box.cell_id} '{box.label}' intersects {other.cell_id} '{other.label}' with padding {padding}.")

    badge_signatures: dict[tuple[object, ...], list[str]] = {}
    for box in boxes:
        if not is_step_badge(box):
            continue
        badge_style = parse_style(box.style)
        signature = (
            round(box.w, 2),
            round(box.h, 2),
            badge_style.get("fillColor", "default").lower(),
            badge_style.get("strokeColor", "default").lower(),
            badge_style.get("fontSize", "default").lower(),
            badge_style.get("fontColor", "default").lower(),
            badge_style.get("fontStyle", "default").lower(),
            badge_style.get("fontFamily", "default").lower(),
            badge_style.get("align", "center").lower(),
            badge_style.get("verticalAlign", "middle").lower(),
        )
        badge_signatures.setdefault(signature, []).append(box.cell_id)
    if len(badge_signatures) > 1:
        detail = "; ".join(f"{signature}: {ids}" for signature, ids in badge_signatures.items())
        warnings.append(
            f"Numbered step badges use inconsistent size or styling ({detail}). Use one badge signature across every sequence track."
        )

    for container in boxes:
        if (
            not container.is_container
            or container.h < 120
            or "legend" in container.cell_id.lower()
            or "qa-layout-exempt" in container.tags
        ):
            continue
        descendants = [
            box
            for box in boxes
            if box.cell_id != container.cell_id and is_ancestor(container.cell_id, box)
        ]
        rails = [
            box
            for box in descendants
            if box.h >= container.h * 0.75 and box.w <= container.w * 0.25
        ]
        usable_left = max((rail.right + 16 for rail in rails), default=container.left + 16)
        usable_right = container.right - 16
        functional = [
            box
            for box in descendants
            if box not in rails
            and not box.is_container
            and not box.style.lower().startswith("text;")
            and "shape=line" not in box.style.lower()
        ]
        if len(functional) < 3 or usable_right <= usable_left:
            continue
        content_left = min(box.left for box in functional)
        content_right = max(box.right for box in functional)
        left_gap = max(0.0, content_left - usable_left)
        right_gap = max(0.0, usable_right - content_right)
        usable_width = usable_right - usable_left
        gap_limit = max(180.0, usable_width * 0.18)
        if left_gap > gap_limit or right_gap > gap_limit:
            warnings.append(
                f"Zone {container.cell_id} has unbalanced horizontal utilization "
                f"(left gap {left_gap:.1f}px, right gap {right_gap:.1f}px within {usable_width:.1f}px usable width); "
                "redistribute functional groups or reduce the boundary."
            )

    standalone_flow_labels: dict[str, list[Box]] = {}
    for box in boxes:
        for tag in box.tags:
            if tag.startswith("qa-flow-label:"):
                edge_id = tag.split(":", 1)[1].strip()
                if edge_id:
                    standalone_flow_labels.setdefault(edge_id, []).append(box)

    for edge in edges:
        polyline = edge_polyline(edge, boxes_by_id)
        if len(polyline) < 2:
            warnings.append(f"Edge {edge.cell_id} has no usable source/target/points.")
            continue

        if edge.target and edge.target in boxes_by_id:
            issue = terminal_entry_issue(edge, boxes_by_id[edge.target])
            if issue:
                errors.append(f"Terminal direction: edge {edge.cell_id} {issue}.")
        if edge.source and edge.source in boxes_by_id:
            issue = initial_exit_issue(edge, boxes_by_id[edge.source])
            if issue:
                errors.append(f"Initial direction: edge {edge.cell_id} {issue}.")

        style = parse_style(edge.style)
        style_ci = {key.lower(): value.lower() for key, value in style.items()}
        associated_labels = [box for box in standalone_flow_labels.get(edge.cell_id, []) if box.label]
        if "qa-labeled-flow" in edge.tags and not edge.label and not associated_labels:
            errors.append(
                f"Labeled flow: edge {edge.cell_id} is tagged qa-labeled-flow but has no inline label or non-empty qa-flow-label:{edge.cell_id} text vertex."
            )
        if edge.label and diagram_type in {"overview", "detailed"}:
            background = style_ci.get("labelbackgroundcolor", "none")
            if background not in {"", "none", "default"}:
                warnings.append(
                    f"Edge {edge.cell_id} label '{edge.label}' uses opaque background {background}; keep relationship labels transparent and fix the route instead of masking it."
                )
            if "qa-labeled-flow" in edge.tags:
                if abs(edge.label_offset_y) < 14.0:
                    warnings.append(
                        f"Edge {edge.cell_id} label '{edge.label}' has only {abs(edge.label_offset_y):.1f}px perpendicular offset; use at least 14px or a transparent standalone text vertex so the connector cannot touch the glyph box."
                    )
                orthogonal_lengths = [
                    abs(b[0] - a[0]) + abs(b[1] - a[1])
                    for a, b in pairwise(polyline)
                    if math.isclose(a[0], b[0], abs_tol=1e-9)
                    or math.isclose(a[1], b[1], abs_tol=1e-9)
                ]
                if not orthogonal_lengths and "orthogonal" in style_ci.get("edgestyle", ""):
                    for a, b in pairwise(polyline):
                        orthogonal_lengths.extend(
                            length
                            for length in (abs(b[0] - a[0]), abs(b[1] - a[1]))
                            if length > 0
                        )
                estimated_label_span = min(240.0, max(48.0, len(edge.label) * 5.5 + 16.0))
                if orthogonal_lengths and max(orthogonal_lengths) < estimated_label_span:
                    warnings.append(
                        f"Edge {edge.cell_id} label '{edge.label}' has no clear segment long enough for its estimated {estimated_label_span:.0f}px span; widen the gutter, wrap the label, or use a standalone text vertex."
                    )
        if "exitX" in style or "exitY" in style:
            if style.get("exitPerimeter") != "1" or parse_float(style.get("sourcePerimeterSpacing"), float("nan")) != 0.0:
                warnings.append(
                    f"Edge {edge.cell_id} constrains its source port but does not explicitly set exitPerimeter=1 and sourcePerimeterSpacing=0."
                )
        if "entryX" in style or "entryY" in style:
            if style.get("entryPerimeter") != "1" or parse_float(style.get("targetPerimeterSpacing"), float("nan")) != 0.0:
                warnings.append(
                    f"Edge {edge.cell_id} constrains its target port but does not explicitly set entryPerimeter=1 and targetPerimeterSpacing=0."
                )

        bends = bend_count(polyline)
        direct_length = 0.0
        if edge.source and edge.source in boxes_by_id and edge.target and edge.target in boxes_by_id:
            direct_length = manhattan_length([boxes_by_id[edge.source].center, boxes_by_id[edge.target].center])
        route_length = manhattan_length(polyline)
        if bends > 4:
            warnings.append(f"Edge {edge.cell_id} uses {bends} bends; simplify the route or document why the detour is meaningful.")
        if direct_length > 0 and route_length / direct_length > 1.75:
            warnings.append(
                f"Edge {edge.cell_id} route is {route_length / direct_length:.2f}x the direct Manhattan distance; use the nearest clear lane."
            )
        if "qa-response-flow" in edge.tags:
            if bends > 2:
                warnings.append(
                    f"Response edge {edge.cell_id} uses {bends} bends; keep response paths local with no more than two elbows."
                )
            if direct_length > 0 and route_length / direct_length > 1.5:
                warnings.append(
                    f"Response edge {edge.cell_id} is {route_length / direct_length:.2f}x the direct Manhattan distance; use the nearest response lane."
                )

        for a, b in pairwise(edge.points):
            segment_length = abs(b[0] - a[0]) + abs(b[1] - a[1])
            if 0 < segment_length < 24:
                warnings.append(
                    f"Edge {edge.cell_id} contains a {segment_length:.1f}px waypoint segment; remove the micro-elbow or widen the gutter."
                )

        if edge.points and edge.source and edge.source in boxes_by_id and edge.target and edge.target in boxes_by_id:
            source_box = boxes_by_id[edge.source]
            target_box = boxes_by_id[edge.target]
            aligned = abs(source_box.center[0] - target_box.center[0]) <= 3 or abs(source_box.center[1] - target_box.center[1]) <= 3
            if aligned:
                direct_is_clear = True
                for box in boxes:
                    if "qa-background" in box.tags:
                        continue
                    if box.cell_id in {edge.source, edge.target} or box.is_container:
                        continue
                    if (edge.source and is_ancestor(edge.source, box)) or (edge.target and is_ancestor(edge.target, box)):
                        continue
                    if segment_intersects_rect(source_box.center, target_box.center, box, padding=2.0):
                        direct_is_clear = False
                        break
                if direct_is_clear and route_length > direct_length * 1.15:
                    warnings.append(
                        f"Edge {edge.cell_id} connects aligned components through an unobstructed gutter but still detours; use a straight connector."
                    )

        exempt = {edge.source, edge.target}
        for p1, p2 in pairwise(polyline):
            for box in boxes:
                if "qa-background" in box.tags:
                    continue
                if box.cell_id in exempt:
                    continue
                if box.is_container:
                    continue
                if (edge.source and is_ancestor(edge.source, box)) or (edge.target and is_ancestor(edge.target, box)):
                    continue
                if segment_intersects_rect(p1, p2, box, padding=2.0):
                    errors.append(f"Line crossing: edge {edge.cell_id} segment crosses box {box.cell_id} '{box.label}'.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="QA check a draw.io mxGraphModel file.")
    parser.add_argument("drawio_file", type=Path)
    parser.add_argument("--padding", type=float, default=6.0)
    parser.add_argument(
        "--diagram-type",
        choices=("general", "overview", "detailed"),
        default="general",
        help="Enable workflow composition checks for an overview or detailed request diagram.",
    )
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    try:
        errors, warnings = run_checks(
            args.drawio_file,
            padding=args.padding,
            diagram_type=args.diagram_type,
        )
    except ET.ParseError as exc:
        print(f"ERROR: invalid XML: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors and not args.warn_only:
        print(f"QA failed: {len(errors)} error(s), {len(warnings)} warning(s).", file=sys.stderr)
        return 1

    print(f"QA passed: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
