# Convert a visual reference to editable Draw.io

Use this workflow for screenshots, slide images, whiteboard photos, Mermaid/PlantUML output, PDFs, or another diagram used as a visual reference.

## Separate content from appearance

Analyze the reference along two axes:

- semantic content: actors, components, boundaries, messages, ordering, labels, and annotations;
- visual grammar: hierarchy, grid, spacing, type scale, corner treatment, palette, icon treatment, edge routing, and density.

Do not assume the reference is factually correct. If source material is available, it outranks the reference. Record discrepancies and assumptions in `source_model.json`.

## Choose the conversion goal

- Faithful reconstruction: preserve topology and visual grammar unless it harms readability.
- Architecture correction: preserve recognizable style while fixing semantics and direction.
- Style transfer: apply the reference’s visual grammar to different source-backed content; never copy its component count or topology.

Record the selected goal in `diagram_lock.json.decisions`.

When the reference comes from Microsoft, AWS, or Google Cloud documentation, identify the structural grammar rather than copying pixels: phase columns, nested group semantics, icon-to-label ratio, numbered flow markers, platform bands, and connector conventions. Select the matching visual archetype and resolve icons from the official provider pack. Read [../references/enterprise-reference-style.md](../references/enterprise-reference-style.md).

## Build editable primitives

Recreate cards, shapes, boundaries, labels, and connectors as native mxGraph cells. Sync and embed exact logos individually. Do not use the reference bitmap as a hidden background or final flattened layer.

When the input is a sequence or flowchart source language, preserve IDs/order as evidence where possible. When the input is a screenshot, give reconstructed items stable semantic IDs rather than coordinates-as-identities.

## Compare and verify

Render the reconstructed result at the same aspect ratio. Compare hierarchy, spacing, semantics, marks, and connector direction. Exact pixel copying is not the goal unless explicitly requested; editability and communication quality remain required.

Complete the same hash-bound `nexcanvas generate` and explicit visual-review
gates as a new diagram. State which elements were copied, inferred, corrected,
or omitted.
