from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .assets import load_manifest, mark_assets, svg_data_uri
from .archetypes import resolve_archetype
from .common import load_json, portable_path, sha256_json, utc_now
from .contracts import validate_diagram_model
from .intents import resolve_view_intent
from .layout import EdgeRoute, Rect, layout_model
from .registry import resolve_route, resolve_theme


NODE_ACCENTS = {
    "actor": "primary",
    "person": "primary",
    "service": "primary",
    "component": "primary",
    "container": "primary",
    "api": "primary",
    "agent": "secondary",
    "model": "secondary",
    "gateway": "warning",
    "decision": "warning",
    "database": "data",
    "datastore": "data",
    "dataset": "data",
    "store": "data",
    "queue": "secondary",
    "event": "secondary",
    "start-event": "data",
    "end-event": "error",
}


def _style(parts: list[str]) -> str:
    return ";".join(part for part in parts if part) + ";"


def _label(node: dict[str, Any], archetype: dict[str, Any] | None = None) -> str:
    title = html.escape(str(node.get("label", "")))
    presentation = str(node.get("presentation") or (archetype or {}).get("nodePresentation", ""))
    if archetype and archetype.get("nodePresentation") == "service-icon" and presentation in {"service-icon", "service-tile", "compact-glyph", "note"}:
        caption = html.escape(str(node.get("caption") or node.get("description") or ""))
        lines = [f"<b>{title}</b>"]
        if caption:
            lines.append(f"<font color='#4A4A4A' size='2'>{caption}</font>")
        return "<br>".join(lines)
    kind = html.escape(str(node.get("kind", "component")).replace("-", " ").upper())
    technology = html.escape(str(node.get("technology", "")))
    description = html.escape(str(node.get("description", "")))
    fields = [html.escape(str(value)) for value in node.get("fields", [])]
    lines = [f"<b>{title}</b>", f"<font color='#64748B' size='2'>{kind}{' · ' + technology if technology else ''}</font>"]
    if description:
        lines.append(f"<font size='2'>{description}</font>")
    if fields:
        lines.append("<div align='left'><font face='monospace' size='2'>" + "<br>".join(fields) + "</font></div>")
    return "<br>".join(lines)


def _boundary_style(
    theme: dict[str, Any],
    boundary: dict[str, Any],
    archetype: dict[str, Any] | None = None,
    layout_strategy: str = "",
) -> str:
    kind = str(boundary.get("kind", "boundary")).lower()
    presentation = str(boundary.get("presentation", kind)).lower()
    if presentation in {"phase-column", "phase", "stage"} and layout_strategy == "compact-pipeline":
        presentation = "outline-phase"
    elif presentation in {"phase-column", "phase", "stage"} and layout_strategy == "phase-rows":
        presentation = "phase-row"
    if archetype and archetype.get("boundaryPresentation") == "phase-column":
        if presentation == "outline-phase":
            return _style(
                [
                    "swimlane", "html=1", "whiteSpace=wrap", "horizontal=1", "startSize=38", "rounded=0",
                    "fillColor=#FFFFFF", "swimlaneFillColor=#FFFFFF",
                    f"strokeColor={archetype.get('groupStroke', theme['border'])}", "strokeWidth=1",
                    f"fontColor={theme['text']}", f"fontFamily={theme['fontFamily']}", "fontStyle=1", "fontSize=14",
                    "align=center", "verticalAlign=middle", "shadow=0", "collapsible=0",
                ]
            )
        if presentation == "phase-row":
            order = int(float(boundary.get("order", 1)))
            fill = archetype.get("stageAltFill") if order % 2 == 0 else archetype.get("stageFill")
            return _style(
                [
                    "swimlane", "html=1", "whiteSpace=wrap", "horizontal=0", "startSize=132", "rounded=0",
                    f"fillColor={fill}", f"swimlaneFillColor={fill}", "strokeColor=none",
                    f"fontColor={theme['text']}", f"fontFamily={theme['fontFamily']}", "fontStyle=1", "fontSize=14",
                    "align=center", "verticalAlign=middle", "shadow=0", "collapsible=0",
                ]
            )
        if presentation in {"phase-column", "phase", "stage"}:
            order = int(float(boundary.get("order", 1)))
            fill = archetype.get("stageAltFill") if order % 2 == 0 else archetype.get("stageFill")
            return _style(
                [
                    "swimlane",
                    "html=1",
                    "whiteSpace=wrap",
                    "horizontal=1",
                    "startSize=38",
                    "rounded=0",
                    f"fillColor={fill}",
                    f"swimlaneFillColor={fill}",
                    "strokeColor=none",
                    f"fontColor={theme['text']}",
                    f"fontFamily={theme['fontFamily']}",
                    "fontStyle=1",
                    "fontSize=14",
                    "align=center",
                    "verticalAlign=middle",
                    "shadow=0",
                    "collapsible=0",
                ]
            )
        if presentation in {"foundation-band", "foundation", "platform"}:
            fill = archetype.get("foundationFill", theme["surfaceAlt"])
            return _style(
                [
                    "swimlane",
                    "html=1",
                    "whiteSpace=wrap",
                    "horizontal=0",
                    "startSize=132",
                    "rounded=0",
                    f"fillColor={fill}",
                    f"swimlaneFillColor={fill}",
                    "strokeColor=none",
                    f"fontColor={theme['text']}",
                    f"fontFamily={theme['fontFamily']}",
                    "fontStyle=1",
                    "fontSize=14",
                    "align=center",
                    "verticalAlign=middle",
                    "shadow=0",
                    "collapsible=0",
                ]
            )
        if presentation == "hub-ring":
            return _style(
                [
                    "ellipse",
                    "container=1",
                    "html=1",
                    "whiteSpace=wrap",
                    "rounded=0",
                    "fillColor=#FFFFFF",
                    f"strokeColor={archetype.get('edgeColor', '#1F1F1F')}",
                    "strokeWidth=1.6",
                    f"fontColor={theme['text']}",
                    f"fontFamily={theme['fontFamily']}",
                    "fontStyle=1",
                    "fontSize=13",
                    "align=center",
                    "verticalAlign=top",
                    "spacingTop=14",
                    "shadow=0",
                    "collapsible=0",
                ]
            )
        if presentation in {"dashed-group", "solid-group", "provider-boundary"}:
            dashed = "1" if presentation == "dashed-group" else "0"
            return _style(
                [
                    "swimlane",
                    "html=1",
                    "whiteSpace=wrap",
                    "horizontal=1",
                    "startSize=30",
                    "rounded=0",
                    f"fillColor={archetype.get('groupFill', '#FFFFFF')}",
                    f"swimlaneFillColor={archetype.get('groupFill', '#FFFFFF')}",
                    f"strokeColor={archetype.get('groupStroke', theme['border'])}",
                    "strokeWidth=1",
                    f"dashed={dashed}",
                    "dashPattern=5 4" if dashed == "1" else "",
                    f"fontColor={theme['text']}",
                    f"fontFamily={theme['fontFamily']}",
                    "fontStyle=1",
                    "fontSize=12",
                    "collapsible=0",
                ]
            )
    dashed = "1" if kind in {"trust", "trust-boundary", "external", "zone"} else "0"
    return _style(
        [
            "swimlane",
            "html=1",
            "whiteSpace=wrap",
            "horizontal=1",
            "startSize=34",
            f"rounded={1 if theme['radius'] else 0}",
            f"arcSize={min(20, int(theme['radius']) * 2)}",
            f"fillColor={theme['surfaceAlt']}",
            f"swimlaneFillColor={theme['surface']}",
            f"strokeColor={theme['border']}",
            f"fontColor={theme['text']}",
            f"fontFamily={theme['fontFamily']}",
            "fontStyle=1",
            "fontSize=13",
            f"dashed={dashed}",
            "dashPattern=6 4" if dashed == "1" else "",
            "shadow=0",
            "collapsible=0",
        ]
    )


def _node_style(
    node: dict[str, Any],
    theme: dict[str, Any],
    asset: dict[str, Any] | None,
    project_root: Path | None,
    archetype: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    kind = str(node.get("kind", "component")).lower()
    presentation = str(node.get("presentation") or (archetype or {}).get("nodePresentation", ""))
    accent_name = NODE_ACCENTS.get(kind, "primary")
    accent = theme.get(accent_name, theme["primary"])
    shape = "roundRect"
    extra: list[str] = []
    if kind in {"database", "datastore", "dataset", "store"}:
        shape = "cylinder3"
        extra.append("size=12")
    elif kind in {"queue", "event-stream"}:
        shape = "hexagon"
    elif kind in {"decision", "gateway"}:
        shape = "rhombus"
    elif kind in {"actor", "person"}:
        shape = "mxgraph.basic.user"
    elif kind in {"start-event", "end-event", "event"}:
        shape = "ellipse"
    elif kind in {"document"}:
        shape = "document"

    embedded = False
    reference_mode = bool(archetype and archetype.get("nodePresentation") == "service-icon")
    reference_icon = reference_mode and presentation in {"service-icon", "service-tile", "compact-glyph"}
    icon_size = 44 if presentation == "compact-glyph" else (48 if presentation == "service-tile" else 56)
    reference_extra: list[str] = []
    if asset:
        if asset.get("localPath") and project_root:
            asset_path = project_root / str(asset["localPath"])
            if asset_path.is_file():
                extra.extend(
                    [
                        "shape=label",
                        f"image={svg_data_uri(asset_path)}",
                        "imageWidth=30",
                        "imageHeight=30",
                        "imageAlign=left",
                        "imageVerticalAlign=middle",
                        "spacingLeft=42",
                    ]
                )
                if reference_icon:
                    reference_extra = [
                        "shape=label",
                        f"image={svg_data_uri(asset_path)}",
                        f"imageWidth={icon_size}",
                        f"imageHeight={icon_size}",
                        "imageAlign=center",
                        "imageVerticalAlign=top",
                        f"spacingTop={icon_size + 6}",
                    ]
                shape = ""
                embedded = True
        elif asset.get("nativeStyle"):
            extra.append(str(asset["nativeStyle"]).rstrip(";"))
            shape = ""

    if reference_mode and presentation == "note":
        return _style(
            [
                "text",
                "html=1",
                "whiteSpace=wrap",
                "align=left",
                "verticalAlign=middle",
                "rounded=0",
                "fillColor=#FFF4CE",
                "strokeColor=none",
                f"fontColor={theme['text']}",
                f"fontFamily={theme['fontFamily']}",
                f"fontSize={theme['bodySize']}",
                "spacing=8",
            ]
        ), embedded

    if reference_icon:
        tile = presentation == "service-tile"
        return _style(
            [
                *(reference_extra or extra),
                "html=1",
                "whiteSpace=wrap",
                "align=center",
                "verticalAlign=bottom",
                "rounded=0",
                f"fillColor={'#FFFFFF' if tile else 'none'}",
                f"strokeColor={archetype.get('groupStroke', theme['border']) if tile else 'none'}",
                f"strokeWidth={1 if tile else 0}",
                f"fontColor={theme['text']}",
                f"fontFamily={theme['fontFamily']}",
                f"fontSize={theme['bodySize']}",
                "spacingBottom=2",
                "shadow=0",
            ]
        ), embedded

    base = [
        f"shape={shape}" if shape else "",
        "html=1",
        "whiteSpace=wrap",
        "align=center",
        "verticalAlign=middle",
        f"rounded={1 if theme['radius'] else 0}",
        f"arcSize={min(20, int(theme['radius']) * 2)}",
        f"fillColor={theme['surface']}",
        f"strokeColor={accent}",
        "strokeWidth=2",
        f"fontColor={theme['text']}",
        f"fontFamily={theme['fontFamily']}",
        f"fontSize={theme['bodySize']}",
        f"shadow={1 if theme.get('shadow') else 0}",
        "spacing=8",
        *extra,
    ]
    return _style(base), embedded


def _edge_style(
    edge: dict[str, Any], theme: dict[str, Any], route: EdgeRoute, archetype: dict[str, Any] | None = None
) -> str:
    kind = str(edge.get("kind", "sync")).lower()
    if archetype and archetype.get("edgePresentation") == "neutral-orthogonal":
        line_class = str(edge.get("lineClass", "control")).lower()
        dashed = "1" if line_class in {"optional", "dependency"} or edge.get("async") else "0"
        color = archetype.get("dataEdgeColor") if line_class == "data" else archetype.get("edgeColor", "#1F1F1F")
        return _style(
            [
                "edgeStyle=orthogonalEdgeStyle",
                "rounded=0",
                "orthogonalLoop=1",
                "jettySize=auto",
                "html=1",
                f"strokeColor={color}",
                "strokeWidth=1.6",
                f"dashed={dashed}",
                "dashPattern=7 5" if dashed == "1" else "",
                "endArrow=block",
                "endFill=1",
                f"fontColor={theme['text']}",
                f"fontFamily={theme['fontFamily']}",
                "fontSize=11",
                "labelBackgroundColor=none",
                f"exitX={route.exit_x}",
                f"exitY={route.exit_y}",
                "exitDx=0",
                "exitDy=0",
                "exitPerimeter=1",
                "sourcePerimeterSpacing=0",
                f"entryX={route.entry_x}",
                f"entryY={route.entry_y}",
                "entryDx=0",
                "entryDy=0",
                "entryPerimeter=1",
                "targetPerimeterSpacing=0",
            ]
        )
    color = theme["primary"]
    dashed = "0"
    end_arrow = "block"
    width = "2"
    if edge.get("async") or kind in {"async", "event", "publish", "subscribe"}:
        color = theme["secondary"]
        dashed = "1"
    if kind in {"data", "read", "write", "lineage", "retrieval"}:
        color = theme["data"]
    if kind in {"risk", "deny", "failure", "threat"}:
        color = theme["error"]
    if kind in {"association", "reference"}:
        dashed = "1"
        end_arrow = "open"
        width = "1.5"
    if kind in {"inheritance"}:
        end_arrow = "blockThin"
    return _style(
        [
            "edgeStyle=orthogonalEdgeStyle",
            "rounded=1",
            "orthogonalLoop=1",
            "jettySize=auto",
            "html=1",
            f"strokeColor={color}",
            f"strokeWidth={width}",
            f"dashed={dashed}",
            "dashPattern=6 4" if dashed == "1" else "",
            f"endArrow={end_arrow}",
            "endFill=1",
            f"fontColor={theme['text']}",
            f"fontFamily={theme['fontFamily']}",
            "fontSize=11",
            "labelBackgroundColor=none",
            f"exitX={route.exit_x}",
            f"exitY={route.exit_y}",
            "exitDx=0",
            "exitDy=0",
            "exitPerimeter=1",
            "sourcePerimeterSpacing=0",
            f"entryX={route.entry_x}",
            f"entryY={route.entry_y}",
            "entryDx=0",
            "entryDy=0",
            "entryPerimeter=1",
            "targetPerimeterSpacing=0",
        ]
    )


def _geometry(cell: ET.Element, rect: Rect) -> None:
    ET.SubElement(
        cell,
        "mxGeometry",
        {"x": f"{rect.x:.1f}", "y": f"{rect.y:.1f}", "width": f"{rect.w:.1f}", "height": f"{rect.h:.1f}", "as": "geometry"},
    )


def _edge_geometry(cell: ET.Element, route: EdgeRoute, edge: dict[str, Any]) -> None:
    geometry = ET.SubElement(
        cell,
        "mxGeometry",
        {
            "relative": "1",
            "as": "geometry",
        },
    )
    if len(route.points) > 2:
        points = ET.SubElement(geometry, "Array", {"as": "points"})
        for x, y in route.points[1:-1]:
            ET.SubElement(points, "mxPoint", {"x": f"{x:.1f}", "y": f"{y:.1f}"})


def _edge_label(edge: dict[str, Any], reference: bool = False) -> str:
    pieces = [str(edge.get("label", "")).strip()]
    if edge.get("annotation"):
        pieces.append(str(edge["annotation"]).strip())
    if reference:
        return "\n".join(piece for piece in pieces if piece)
    technical = " · ".join(str(edge.get(key, "")).strip() for key in ("protocol", "payload") if edge.get(key))
    if technical:
        pieces.append(technical)
    if edge.get("authority"):
        pieces.append(f"auth: {edge['authority']}")
    return "\n".join(piece for piece in pieces if piece)


def _edge_label_mode(edge: dict[str, Any], label: str) -> str:
    if not label:
        return "none"
    return str(edge.get("labelMode", "offset")).strip().lower()


def _edge_label_rect(edge: dict[str, Any], route: EdgeRoute, label: str, mode: str) -> Rect:
    placement = edge.get("labelPlacement") if isinstance(edge.get("labelPlacement"), dict) else {}
    edge_layout = edge.get("layout") if isinstance(edge.get("layout"), dict) else {}
    lines = label.splitlines() or [label]
    longest = max((len(line) for line in lines), default=1)
    horizontal_padding = 16.0 if mode == "callout" else 8.0
    vertical_padding = 8.0 if mode == "callout" else 4.0
    estimated_width = min(300.0, max(54.0, longest * 6.1 + horizontal_padding))
    estimated_height = max(20.0, len(lines) * 14.0 + vertical_padding)
    width = float(placement.get("width", estimated_width))
    height = float(placement.get("height", estimated_height))

    segment_value = placement.get("segment", edge_layout.get("labelSegment"))
    try:
        segment = max(0, min(len(route.points) - 2, int(segment_value))) if segment_value is not None else None
    except (TypeError, ValueError):
        segment = None
    if segment is None:
        candidates = list(enumerate(zip(route.points, route.points[1:])))
        horizontal = [
            (index, points)
            for index, points in candidates
            if abs(points[0][1] - points[1][1]) <= 0.5
        ]
        pool = horizontal or candidates
        segment, _ = max(
            pool,
            key=lambda item: abs(item[1][1][0] - item[1][0][0]) + abs(item[1][1][1] - item[1][0][1]),
        )
    start = route.points[segment]
    end = route.points[segment + 1]
    try:
        t = max(0.0, min(1.0, float(placement.get("t", edge_layout.get("labelT", 0.5)))))
    except (TypeError, ValueError):
        t = 0.5
    center_x = start[0] + (end[0] - start[0]) * t
    center_y = start[1] + (end[1] - start[1]) * t
    is_horizontal = abs(start[1] - end[1]) <= abs(start[0] - end[0])

    side = str(placement.get("side", "center" if mode == "callout" else "auto")).lower()
    try:
        offset = max(0.0, float(placement.get("offset", 8.0 if mode == "offset" else 12.0)))
    except (TypeError, ValueError):
        offset = 8.0 if mode == "offset" else 12.0
    if side == "auto":
        side = "above" if is_horizontal else "right"
    if side == "above":
        center_y -= height / 2.0 + offset
    elif side == "below":
        center_y += height / 2.0 + offset
    elif side == "left":
        center_x -= width / 2.0 + offset
    elif side == "right":
        center_x += width / 2.0 + offset

    try:
        center_x += float(placement.get("dx", 0.0))
    except (TypeError, ValueError):
        pass
    try:
        center_y += float(placement.get("dy", 0.0))
    except (TypeError, ValueError):
        pass
    return Rect(center_x - width / 2.0, center_y - height / 2.0, width, height)


def _append_flow_label(
    graph_root: ET.Element,
    edge: dict[str, Any],
    route: EdgeRoute,
    label: str,
    mode: str,
    theme: dict[str, Any],
) -> None:
    edge_id = str(edge["id"])
    rect = _edge_label_rect(edge, route, label, mode)
    fill = theme["surface"] if mode == "callout" else "none"
    font_color = theme["muted"] if mode == "note" else theme["text"]
    value = "<br>".join(html.escape(line) for line in label.splitlines())
    cell = ET.SubElement(
        graph_root,
        "mxCell",
        {
            "id": f"label-{edge_id}",
            "value": value,
            "style": _style(
                [
                    "text",
                    "html=1",
                    "whiteSpace=wrap",
                    "align=center",
                    "verticalAlign=middle",
                    f"fillColor={fill}",
                    "strokeColor=none",
                    f"fontColor={font_color}",
                    f"fontFamily={theme['fontFamily']}",
                    "fontSize=11",
                    "fontStyle=2" if mode == "note" else "fontStyle=0",
                    "spacing=4" if mode == "callout" else "spacing=0",
                    "rounded=0",
                    "shadow=0",
                ]
            ),
            "vertex": "1",
            "parent": "1",
            "nc-kind": "flow-label",
            "nc-edge-id": f"edge-{edge_id}",
            "nc-label-mode": mode,
            "tags": f"qa-flow-label:edge-{edge_id} qa-edge-label qa-label-{mode}",
        },
    )
    _geometry(cell, rect)


def build_tree(model: dict[str, Any], project_root: Path | None = None, root: Path | None = None) -> tuple[ET.ElementTree, set[str]]:
    issues = validate_diagram_model(model, root)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ValueError("Invalid diagram model:\n" + "\n".join(f"- {issue.location}: {issue.message}" for issue in errors))
    route = resolve_route(model["route"]["family"], model["route"]["profile"], root)
    theme = resolve_theme(model["theme"], root)
    archetype = resolve_archetype(str(model.get("visualArchetype", "")) or None, root)
    layout_adapter = str(archetype.get("layoutAdapter") or route["layout"])
    layout = layout_model(model, layout_adapter)
    canvas = model["canvas"]
    view_intent = resolve_view_intent(model)

    mxfile = ET.Element(
        "mxfile",
        {
            "host": "NexCanvas Draw.io",
            "agent": "nexcanvas-drawio/2.0",
            "version": "2.0",
            "type": "device",
            "modified": utc_now(),
            "nc-model-hash": sha256_json(model),
            "nc-route": f"{model['route']['family']}/{model['route']['profile']}",
            "nc-view-intent": view_intent,
            "nc-visual-archetype": str(archetype["key"]),
            "nc-layout-strategy": str(model.get("layoutStrategy", "auto")),
            "pageWidth": str(canvas["width"]),
            "pageHeight": str(canvas["height"]),
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"id": "nexcanvas-page-1", "name": view_intent.replace("-", " ").title()})
    graph = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1422",
            "dy": "794",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(canvas["width"]),
            "pageHeight": str(canvas["height"]),
            "math": "0",
            "shadow": "0",
            "background": str(canvas.get("background") or theme["canvas"]),
        },
    )
    graph_root = ET.SubElement(graph, "root")
    ET.SubElement(graph_root, "mxCell", {"id": "0"})
    ET.SubElement(graph_root, "mxCell", {"id": "1", "parent": "0"})
    background = ET.SubElement(
        graph_root,
        "mxCell",
        {
            "id": "nc-background",
            "value": "",
            "style": _style([f"fillColor={canvas.get('background') or theme['canvas']}", "strokeColor=none", "pointerEvents=0", "locked=1"]),
            "vertex": "1",
            "parent": "1",
            "nc-kind": "background",
            "tags": "qa-background",
        },
    )
    _geometry(background, Rect(0.0, 0.0, float(canvas["width"]), float(canvas["height"])))

    if model.get("showTitle", True):
        title_value = f"<b>{html.escape(model['title'])}</b>"
        if model.get("subtitle"):
            title_value += f"<br><font size='3' color='{theme['muted']}'>{html.escape(str(model['subtitle']))}</font>"
        title_cell = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": "nc-title",
                "value": title_value,
                "style": _style(["text", "html=1", "align=left", "verticalAlign=middle", "whiteSpace=wrap", "strokeColor=none", "fillColor=none", f"fontColor={theme['text']}", f"fontFamily={theme['fontFamily']}", f"fontSize={theme['titleSize']}"]),
                "vertex": "1",
                "parent": "1",
                "nc-kind": "title",
                "tags": "qa-illustrative",
            },
        )
        title_width = float(canvas["width"]) - (520.0 if model.get("legend") else 116.0)
        _geometry(title_cell, Rect(58.0, 28.0, title_width, 66.0))

    boundary_by_id = {str(item["id"]): item for item in model.get("boundaries", [])}

    def boundary_depth(item: dict[str, Any]) -> int:
        depth = 0
        parent = item.get("parent")
        visited: set[str] = set()
        while parent and str(parent) in boundary_by_id and str(parent) not in visited:
            visited.add(str(parent))
            depth += 1
            parent = boundary_by_id[str(parent)].get("parent")
        return depth

    for boundary in sorted(model.get("boundaries", []), key=lambda item: (boundary_depth(item), str(item.get("id")))):
        rect = layout.boundaries.get(str(boundary["id"]))
        if not rect:
            continue
        parent_id = str(boundary.get("parent", ""))
        parent_rect = layout.boundaries.get(parent_id)
        local_rect = Rect(rect.x - parent_rect.x, rect.y - parent_rect.y, rect.w, rect.h) if parent_rect else rect
        boundary_presentation = str(boundary.get("presentation", boundary.get("kind", ""))).lower()
        foundation_reference = (
            archetype.get("boundaryPresentation") == "phase-column"
            and boundary_presentation in {"foundation-band", "foundation", "platform"}
        )
        cell = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": f"boundary-{boundary['id']}",
                "value": "" if foundation_reference else str(boundary["label"]),
                "style": _boundary_style(theme, boundary, archetype, str(model.get("layoutStrategy", ""))),
                "vertex": "1",
                "parent": f"boundary-{parent_id}" if parent_rect else "1",
                "nc-kind": "boundary",
                "nc-boundary-kind": str(boundary.get("kind", "boundary")),
                "nc-model-id": str(boundary["id"]),
                "qa-container": "true",
                "tags": "qa-container",
            },
        )
        _geometry(cell, local_rect)
        if foundation_reference:
            label_cell = ET.SubElement(
                graph_root,
                "mxCell",
                {
                    "id": f"boundary-label-{boundary['id']}",
                    "value": f"<b>{html.escape(str(boundary['label']))}</b>",
                    "style": _style(
                        [
                            "text",
                            "html=1",
                            "whiteSpace=wrap",
                            "align=center",
                            "verticalAlign=middle",
                            "strokeColor=none",
                            "fillColor=none",
                            f"fontColor={theme['text']}",
                            f"fontFamily={theme['fontFamily']}",
                            "fontSize=14",
                        ]
                    ),
                    "vertex": "1",
                    "parent": f"boundary-{boundary['id']}",
                    "nc-kind": "boundary-label",
                    "tags": "qa-illustrative",
                },
            )
            _geometry(label_cell, Rect(0.0, 0.0, 132.0, rect.h))

    manifest_assets: dict[str, dict[str, Any]] = {}
    if project_root and (project_root / "assets" / "asset_manifest.json").is_file():
        manifest_assets = {str(item.get("key")): item for item in load_manifest(project_root, root).get("assets", [])}
    embedded_keys: set[str] = set()
    for node in model.get("nodes", []):
        node_id = str(node["id"])
        rect = layout.nodes[node_id]
        boundary_id = str(node.get("boundary", ""))
        boundary_rect = layout.boundaries.get(boundary_id)
        local_rect = Rect(rect.x - boundary_rect.x, rect.y - boundary_rect.y, rect.w, rect.h) if boundary_rect else rect
        asset_key = str(node.get("assetRef", ""))
        style, embedded = _node_style(node, theme, manifest_assets.get(asset_key), project_root, archetype)
        if embedded:
            embedded_keys.add(asset_key)
        cell = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": f"node-{node_id}",
                "value": _label(node, archetype),
                "style": style,
                "vertex": "1",
                "parent": f"boundary-{boundary_id}" if boundary_rect else "1",
                "nc-kind": "node",
                "nc-node-kind": str(node.get("kind", "component")),
                "nc-model-id": node_id,
                "nc-boundary": str(node.get("boundary", "")),
                "nc-asset-ref": asset_key,
                "qa-primary": "true" if node.get("importance") == "primary" else "false",
                "tags": "qa-primary" if node.get("importance") == "primary" else ("qa-support" if node.get("importance") == "support" else ""),
            },
        )
        _geometry(cell, local_rect)

    if layout.adapter == "sequence":
        lifeline_bottom = float(canvas["height"]) - 120.0
        for node in model.get("nodes", []):
            rect = layout.nodes[str(node["id"])]
            cell = ET.SubElement(
                graph_root,
                "mxCell",
                {
                    "id": f"lifeline-{node['id']}",
                    "value": "",
                    "style": _style(["edgeStyle=none", "html=1", "dashed=1", "dashPattern=4 4", f"strokeColor={theme['border']}", "endArrow=none", "startArrow=none"]),
                    "edge": "1",
                    "parent": "1",
                    "nc-kind": "lifeline",
                },
            )
            geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            ET.SubElement(geometry, "mxPoint", {"x": f"{rect.cx:.1f}", "y": f"{rect.bottom:.1f}", "as": "sourcePoint"})
            ET.SubElement(geometry, "mxPoint", {"x": f"{rect.cx:.1f}", "y": f"{lifeline_bottom:.1f}", "as": "targetPoint"})

    flow_label_specs: list[tuple[dict[str, Any], EdgeRoute, str, str]] = []
    step_badge_specs: list[tuple[dict[str, Any], EdgeRoute]] = []
    for edge in model.get("edges", []):
        edge_id = str(edge["id"])
        route_geometry = layout.edges.get(edge_id)
        if not route_geometry:
            continue
        rendered_label = _edge_label(edge, archetype.get("edgePresentation") == "neutral-orthogonal")
        label_mode = _edge_label_mode(edge, rendered_label)
        has_visible_label = bool(rendered_label and label_mode != "none")
        cell = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": f"edge-{edge_id}",
                "value": "",
                "style": _edge_style(edge, theme, route_geometry, archetype),
                "edge": "1",
                "parent": "1",
                "source": f"node-{edge['source']}",
                "target": f"node-{edge['target']}",
                "nc-kind": "edge",
                "nc-edge-kind": str(edge.get("kind", "sync")),
                "nc-model-id": edge_id,
                "nc-label-mode": label_mode,
                "nc-bus-id": str(edge.get("busId", "")),
                "nc-lane-id": str(edge.get("laneId", "")),
                "nc-allow-crossing": "true" if edge.get("allowCrossing") else "false",
                "nc-trust-crossing": "true" if edge.get("trustCrossing") else "false",
                "qa-edge": "true",
                "tags": " ".join(
                    [
                        "qa-primary-flow" if edge.get("importance") == "primary" else "",
                        "qa-labeled-flow" if has_visible_label else "",
                        "qa-response-flow" if str(edge.get("kind", "")).lower() == "response" else "",
                        "qa-data-flow" if str(edge.get("kind", "")).lower() in {"data", "read", "write", "lineage", "retrieval"} else "",
                        "qa-error-flow" if str(edge.get("kind", "")).lower() in {"risk", "deny", "failure", "threat"} else "",
                        "qa-rail-flow" if isinstance(edge.get("layout"), dict) and edge["layout"].get("rail") is not None else "",
                        "qa-explicit-route" if isinstance(edge.get("layout"), dict) and edge["layout"].get("waypoints") else "",
                    ]
                ).strip(),
            },
        )
        _edge_geometry(cell, route_geometry, edge)
        if has_visible_label:
            flow_label_specs.append((edge, route_geometry, rendered_label, label_mode))

        if edge.get("step") is not None and archetype.get("stepBadgeFill"):
            step_badge_specs.append((edge, route_geometry))

    # Labels and badges are deliberately emitted after every connector. This keeps
    # Microsoft-style callouts and step markers above the line layer while geometry
    # QA still rejects unrelated connectors hidden by those cells.
    for edge, route_geometry, rendered_label, label_mode in flow_label_specs:
        _append_flow_label(graph_root, edge, route_geometry, rendered_label, label_mode, theme)

    for edge, route_geometry in step_badge_specs:
        edge_id = str(edge["id"])
        points = route_geometry.points
        edge_layout = edge.get("layout") if isinstance(edge.get("layout"), dict) else {}
        try:
            segment = max(0, min(len(points) - 2, int(edge_layout.get("badgeSegment", 0))))
        except (TypeError, ValueError):
            segment = 0
        try:
            badge_t = max(0.0, min(1.0, float(edge_layout.get("badgeT", 0.42))))
        except (TypeError, ValueError):
            badge_t = 0.42
        start = points[segment]
        end = points[segment + 1] if len(points) > segment + 1 else points[-1]
        badge_x = start[0] + (end[0] - start[0]) * badge_t
        badge_y = start[1] + (end[1] - start[1]) * badge_t
        badge = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": f"step-{edge_id}",
                "value": html.escape(str(edge["step"])),
                "style": _style(
                    [
                        "ellipse",
                        "html=1",
                        f"fillColor={archetype['stepBadgeFill']}",
                        "strokeColor=none",
                        f"fontColor={archetype.get('stepBadgeText', '#FFFFFF')}",
                        f"fontFamily={theme['fontFamily']}",
                        "fontSize=12",
                        "fontStyle=1",
                        "align=center",
                        "verticalAlign=middle",
                        "shadow=0",
                    ]
                ),
                "vertex": "1",
                "parent": "1",
                "nc-kind": "step-badge",
                "nc-edge-id": edge_id,
                "tags": "qa-step-badge qa-illustrative",
            },
        )
        _geometry(badge, Rect(badge_x - 14.0, badge_y - 14.0, 28.0, 28.0))

    if model.get("legend"):
        legend = "<b>LEGEND</b><br>" + "<br>".join(
            f"{html.escape(str(item['label']))} — {html.escape(str(item['kind']))}" for item in model["legend"]
        )
        cell = ET.SubElement(
            graph_root,
            "mxCell",
            {
                "id": "nc-legend",
                "value": legend,
                "style": _style(["rounded=1", "html=1", "whiteSpace=wrap", "align=left", "verticalAlign=top", f"fillColor={theme['surface']}", f"strokeColor={theme['border']}", f"fontColor={theme['text']}", "fontSize=10", "spacing=8"]),
                "vertex": "1",
                "parent": "1",
                "nc-kind": "legend",
                "tags": "qa-legend",
            },
        )
        _geometry(cell, Rect(float(canvas["width"]) - 410.0, 30.0, 352.0, 62.0))

    return ET.ElementTree(mxfile), embedded_keys


def build_drawio(model_path: Path, output_path: Path, project_root: Path | None = None, root: Path | None = None) -> dict[str, Any]:
    model = load_json(model_path)
    if not isinstance(model, dict):
        raise ValueError("diagram model must be a JSON object")
    tree, embedded_keys = build_tree(model, project_root, root)
    ET.indent(tree, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    if project_root and embedded_keys:
        mark_assets(project_root, embedded_keys, "Embedded")
    return {
        "output": portable_path(output_path, project_root),
        "route": f"{model['route']['family']}/{model['route']['profile']}",
        "nodes": len(model.get("nodes", [])),
        "edges": len(model.get("edges", [])),
        "embeddedAssets": sorted(embedded_keys),
        "modelHash": sha256_json(model),
    }
