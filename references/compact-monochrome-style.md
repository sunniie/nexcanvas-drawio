# Compact Monochrome System Flow

Use this optional visual style when the user supplies a compact black-and-white workflow reference, asks for a clean academic/engineering system flow, or prefers relationship labels over color-coded line classes. It can be applied to either Architecture Overview or Detailed Request Flow. The workflow mode controls information depth; this style controls presentation.

The source image may have been produced by Draw.io, Lucidchart, Figma, or another vector editor. Do not claim tool provenance from a raster screenshot alone. Reproduce the grammar with native Draw.io containers, rounded rectangles, diamonds, cylinders, orthogonal edges, and built-in outline glyphs.

## Visual grammar

- Use a white canvas, white component fills, dark gray or near-black 1.5-2 px strokes, and high-contrast black text.
- Allow one restrained accent color for the outer system frame or the highest ownership boundary. Do not recolor every group.
- Build hierarchy through nesting and shape semantics rather than large colored panels: outer system boundary, functional group, leaf component, decision, and persistent store.
- Use compact rounded rectangles for actors, services, and features; a diamond only for a real branch or gate; cylinders only for persistent stores; and a distinct compact card for an external service.
- Use small outline glyphs at the left of a title when they improve recognition. Keep them stylistically consistent and subordinate to the label.
- Size groups from their children plus deliberate internal padding. Do not inflate a group to create artificial symmetry, and do not copy the reference's group or component count.
- Number events only when sequence order is necessary. A labeled topology or data-flow map does not need badges. When a service boundary contains a real ordered internal lifecycle, use small identical circular badges inside the leaf-card title row. Reset local numbers inside an unmistakably titled boundary or use stable agent prefixes when cross-boundary references would otherwise be ambiguous.
- Compact a one-title/one-detail leaf to roughly 48-56 px high before expanding its parent. Remove decorative glyphs when a step badge already provides the visual anchor, and use the recovered area for connector and annotation lanes.

## Connector and label grammar

- Reserve explicit horizontal and vertical routing gutters before placing cards. Route every connector through those gutters, never through a component, icon, component title, database, or unrelated group header.
- Attach both ends to the visible perimeter. Enter a rectangular card perpendicularly; meet a diamond or cylinder at its actual perimeter; keep a visible straight terminal shaft before the arrowhead.
- Prefer a straight connector when source and target align. Otherwise use a clean orthogonal route with no more than two elbows unless a real obstacle requires more.
- Label an edge with the action, payload, or outcome it carries, such as `Update role`, `Export JSON`, `Save scores`, or `Return result`. Use concise verb-led phrases and keep component responsibilities inside components.
- Omit labels that only paraphrase the source or target card. A clean arrow between `Profile Tool` and `Profile Scanner` is clearer than a cramped `Profile scan` label that adds no new fact.
- Place a label beside the longest clear segment. Keep 6-12 px of visible whitespace from the nearest text edge to the line and at least 6 px from every shape; on a 1920×1080 canvas this normally requires a label-center offset of at least 14 px. Never use the automatic centered edge-label position, and never let the line strike or graze its own text.
- Use transparent labels. Do not hide routing problems with opaque white label backgrounds.
- Keep one semantic fact per connector. If request and response both matter, draw two directional edges and label them separately.
- Put paired request/response annotations on opposite outer sides of their lanes rather than stacking both labels between the connectors.
- Use a shared trunk only for a real fan-out, fan-in, or bus. Add a clear junction or branch origin; reject ambiguous T-junctions that look connected by accident.
- Keep parallel connectors in separate lanes with readable spacing. Never stack several labels on the same segment.

## Composition pattern

1. Put actors and access/authentication near the top when they establish entry and role.
2. Place a decision immediately after the state it evaluates, then branch toward the owning functional groups.
3. Keep peer capability groups in the middle, with leaf components aligned to a simple grid inside each group.
4. Put persistent stores below the components that read or write them; connect vertically or through a shallow data gutter.
5. Place external compute or AI beside the component that invokes it rather than in a distant dependency sidebar.
6. Use labels to make read, write, export, feedback, request, and return semantics explicit. Add a legend only when line styling itself carries multiple meanings.

This is a content-responsive pattern, not a fixed template. Omit any layer that the subject does not contain, and add or reorganize groups when the real ownership or request topology requires it.

## Review checklist

- Can every edge label be read without touching a line, arrowhead, card, or boundary?
- Does every important edge label have an explicit offset or a transparent standalone text vertex, with visible whitespace around every glyph?
- Does every connector have an unambiguous source, target, direction, and meaning?
- Do connectors avoid every unrelated leaf component and group title?
- Are decision branches labeled near the first clear branch segment?
- Are data stores connected only to components that actually read or write them?
- Does nesting communicate real ownership or scope rather than decorative boxing?
- Is the monochrome hierarchy still clear at 100% zoom without relying on color?
- At 200% zoom, do arrowheads stop on the visible perimeter with a straight terminal shaft?
- Are sparse one- or two-line leaves compact, and are ordered agent stages numbered consistently without numbering stores or support services?
