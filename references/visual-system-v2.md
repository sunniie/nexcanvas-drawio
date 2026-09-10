# Visual system v2

## Hierarchy

Design for the target reading distance. Title first, then primary story, then supporting metadata. Use one visual accent per semantic role: primary control, data, secondary/async, warning, error. Do not color every box differently.

Primary content should usually span at least 70% of the canvas dimension aligned with the reading flow. Metadata and legends should remain compact. Large empty cards are not “premium”; size content envelopes to their text and icon.

## Typography

Use portable font stacks from `config/styles.json`; keep fallbacks rather than truncating to a missing first font. Titles are 26–30 px, node text 12–14 px, technical metadata 10–12 px at a 1600×900 baseline. Avoid text smaller than 10 px in final delivery.

Names are concise nouns; relationship labels are active verbs. Put technology/type on a restrained secondary line. Keep long explanations outside the diagram or split the view.

For icon-led nodes, reserve separate vertical bands for the icon and for the title/caption. The caption must begin below the rendered icon box with visible breathing room; never center icon and text independently in the same space. `service-icon` nodes use a minimum 150x112 px envelope, `compact-glyph` 126x92 px, and `service-tile` 160x126 px. Reflow or enlarge the node when the text needs more room instead of shrinking these envelopes.

## Boundaries

Every boundary must mean ownership, trust, runtime, lifecycle, or swimlane responsibility. Use pale fills and stronger headings, with content inside rather than overlapping as unrelated peers. Dashed boundaries indicate trust/external zones only when the notation requires them.

## Connectors

- Attach to the nearest clear perimeter side.
- Use orthogonal segments and dedicated gutters.
- Keep forward flow visually direct; route response/feedback in a separate lane.
- Select `none`, `offset`, `callout`, or `note` per relationship; read [connector-label-routing.md](connector-label-routing.md).
- Give transparent offset/note labels a reserved rectangle and visible stroke clearance. Use an opaque callout only to create an intentional break in its own long rail.
- Keep arrowheads unambiguous and outside target shapes.
- Avoid connector-through-card and connector-through-label crossings.
- Do not share a route segment unless the edges have the same semantic `busId`; assign distinct `laneId` values to parallel flows.
- Prefer separate one-way edges when payload, authority, timing, or failure semantics differ.

Edge meaning is encoded by `kind`: primary sync/control, secondary dashed async, green data/read/write/retrieval, red failure/deny/threat. Legends must match actual styles.

## Layout adapters

- `layered`: dependency/process flow with topological ranks.
- `nested`: ownership/runtime/trust containment.
- `sequence`: participants across top, ordered messages down time.
- `swimlane`: responsibility stages across explicit lanes.
- `rag`: offline and online lanes with separate return/cross-lane routing.
- `reference`: official-documentation phase columns, icon-led services, numbered narrative flows, optional nested groups, and a foundation band.
- `erd`/`grid`: structured entities/cards with stable alignment.
- `matrix`: classifications/capabilities/governance across comparable cells.
- `radial`: one focal subject with non-sequential peers.
- `tree`: hierarchy/information architecture.

Choose the adapter from the route registry; override node size/order only for content-driven tuning. Never use arbitrary absolute coordinates as the primary model.

V3 `presentation.visualArchetype` may deliberately override the route's default layout. For example, `ai-ml/rag` normally uses its offline/online lane adapter, while `microsoft-reference` switches it to the reference adapter. This is a presentation decision; the route still owns semantic QA.

## Themes

Themes are token sets, not fixed templates. All themes preserve semantic roles and minimum 4.5:1 text contrast. Prefer:

- `technical-editorial` for most engineering docs;
- `cloud-reference` for exact cloud/runtime views;
- `blueprint-engineering` for infrastructure/network detail;
- `dark-operations` for control-room/observability contexts;
- `minimal-monochrome` for print and dense reports;
- `executive-layered` for leadership communication;
- `data-lab` for analytical/data/ML views;
- `strict-notation` when notation fidelity outranks decoration.
- `microsoft-reference` only with the `microsoft-reference` visual archetype and official Microsoft service icons.

Themes supply color and typography tokens. Archetypes control composition and object treatment. Changing a theme cannot turn a card grid into a provider reference architecture.

## Visual review

Automated layout is a first composition, not an aesthetic guarantee. Render, inspect, and adjust semantic order, node size, gutters, or route-specific logic. Inspect every icon-led node at 100% and confirm that no title or caption enters the icon bounding box. Approve only the exact artifact hash that was viewed.
