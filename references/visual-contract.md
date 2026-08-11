# Reference Visual Contract

Use this contract for Architecture Overview and Detailed Request workflow diagrams unless the user supplies a newer reference.

Workflow mode and visual style are orthogonal. When the user selects or supplies a compact monochrome, relationship-led reference, also read [compact-monochrome-style.md](compact-monochrome-style.md). Its palette, shape, and connector-label grammar override the colorful defaults below; the shared rejection criteria still apply.

## Architecture Overview grammar

- Use a white or very light gray canvas with a concise title/subtitle and a compact line legend when multiple flow types exist.
- Place the actor and integration chain in a shallow top band inside the major cloud/system boundary.
- Use one dominant processing boundary with a short header and an aligned capability router or entry lane.
- Arrange capabilities as compact nested modules. Each module may contain text-led process cards, decisions, small databases, and one restrained task glyph that communicates its dominant action.
- Put official cloud, AI, storage, vector, and database logos in a shallow resource row directly below the capability that owns them.
- Put assessments, alignment, reporting, or other downstream workflows in a lower row when they are semantically distinct.
- Use bright pale blue, cyan, green, violet, and orange fills with crisp saturated strokes. Keep the primary request dark navy, persistence green dashed, response violet dashed, and validation errors red; avoid washed-out gray-heavy compositions.

## Detailed Request grammar

- Use a faint grid or clean white canvas with horizontal execution/trust bands.
- Give every major band a slim left rail containing a short layer name and 1-2 lines of scope. Keep the rail within roughly 7-10% of canvas width.
- Put the numbered primary journey across the top band. Use identical circular blue badges and concise technology cards with official logos.
- Keep the main request line dark navy and straight. Put the response in a separate nearby violet dashed lane, data/async in green dashed lanes, and telemetry in orange dashed or dotted lanes.
- Place private application components, queues, pods, caches, databases, and object storage in the middle band. Size cards by content and distribute them across the usable width.
- Place observability components in a lower band and show their support flow without numbering them as user-journey events.
- Include a thin footer legend whenever more than one line language is present. Legend samples must exactly match the diagram.
- When one screen contains several interactions, stack concise track bands with independent prefixes instead of forcing a single global number sequence. Each track should read cleanly on its own.
- Put security prerequisites, trust warnings, data exposure, fallbacks, and partial-success notes directly below the stage they qualify. Keep them compact, high-contrast, and connected by a short local line.
- Technology logos must be embedded and visibly rendered. Use an exact verified product icon for a real resource; use a clearly neutral Draw.io glyph for an internal task or concept when no brand identity is intended.

## Shared rejection criteria

- Reject meaningless hero pictograms inside every step, infographic-like scenes, or oversized cards with sparse text. A semantic task glyph is acceptable when it improves stage recognition and remains subordinate to the component content.
- Reject missing official logos for known technologies when a verified icon is available.
- Reject title/legend/sidebar removal when those elements are structural in the selected reference.
- Reject connectors that start or end inside a card, miss the perimeter, reverse terminal direction, cross labels/cards, contain micro-elbows, or take an unexplained detour.
- Reject inconsistent badge color, size, stroke, font, or alignment.
- Reject low-contrast gray text, washed-out strokes, clipped labels, or excessive empty fields inside populated layers.
- Reject false request continuity, hidden client authority, unqualified non-atomic writes, incorrect execution direction, and errors attached to the wrong stage even when the geometry is clean.
- Reject a response, acknowledgement, callback, retry, or feedback label placed on the opposite-direction request edge. Use separate one-way connectors and verify the visible arrowhead direction in the exported image.
- Reject a required relationship connector without its action/payload label, a label placed over a component or group title, a connector running through its own label, or an opaque label background used to conceal a poor route.
- Reject remote-only icon URLs, invisible image cells, or a substitute brand that visually claims to be the named product.
