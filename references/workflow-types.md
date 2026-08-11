# Workflow Diagram Modes

Use this reference only for workflow, architecture, integration, and system-flow requests.

Choose the workflow mode for information depth, then choose a visual style independently through [style-catalog.md](style-catalog.md). Either mode may use Color Visual, Compact Monochrome, or a user-supplied reference.

## Architecture Overview

Choose this mode for README files, slides, portfolios, executive communication, system maps, ownership boundaries, and high-level dependency views.

1. Tell one primary system story. Show actors, major services, real boundaries, data authorities, and downstream consumers without exposing every endpoint or state transition.
2. Prefer a compact integration band plus one dominant processing boundary. Group repeated stages with aligned header strips and place supporting services directly below the stage that uses them.
3. Treat stages as capabilities, not request events. Put optional stage numbers inside headers; do not float event badges above cards.
4. Keep failure matrices, operation names, commit metadata, API catalogs, and implementation fallbacks out of the main canvas. Put provenance outside the artifact and move implementation detail into a Detailed Request diagram.
5. Use nested processing cards for internal capabilities and official logos for the real cloud/data/AI resources below them. Add a neutral Draw.io semantic glyph to selected tasks such as intake, document/OCR, review, scoring, or governance when it improves scanability; do not require or oversize one for every capability.

## Detailed Request Flow

Choose this mode for endpoint behavior, a bounded user interaction, request/response analysis, state changes, retry/failure behavior, or engineering documentation.

1. Define the request or interaction boundary before numbering events. If the subject contains separate HTTP interactions, use separate tracks or lanes; never represent them as one continuous request.
2. Number only active events. Keep databases, AI providers, observability, caches, and passive dependencies unnumbered.
3. Show the primary path first, then user decisions, state transitions, bounded fallbacks, persistence, and local error outcomes. Keep support services visually subordinate.
4. Use one badge signature across every track. Prefix badge identifiers when needed, such as `S1`, `A1`, and `L1`, while keeping diameter, fill, stroke, font, and alignment identical.
5. Route request, response, data, and error flows in independent lanes. Keep response routes close to their source and destination; do not wrap them around the canvas.
6. Use official logos inside technology cards and one consistent badge style for numbered events. Use neutral semantic glyphs for user, browser, document, validation, OCR, decision, review, scoring, persistence, and result nodes when they improve recognition; avoid decorative hero icons without operational meaning.
7. When the system naturally has access, private application/data, and observability layers, use shallow horizontal bands with a slim left title rail. Keep the primary path near the top of each band and support flows in separate lanes.
8. Build an interaction ledger before assigning badges. A page GET, a later browser-only Run action, and a submit POST are three tracks even when they occur in one screen. Prefix their events independently, such as `L1`, `R1`, and `S1`.
9. Mark trust boundaries and authority honestly. If the client computes a score and the server only checks numeric bounds, label the score untrusted and do not imply server-side grading. Surface client-visible secrets, non-atomic writes, ignored errors, and partial-success states near the step that owns them.
10. Model internal order, not just the outer service boundary. Connect validation, reads, writes, fallbacks, reward side effects, and response construction in the order the implementation executes them; attach errors to the stage that can actually emit them.

## Shared composition and QA

- Make primary content occupy most of the useful canvas. A tagged support region should normally stay at or below 25% of usable area; metadata plus legend should normally stay at or below 12% of canvas height.
- Fill a semantic zone by distributing meaningful peer components, not by inflating sparse cards. A large leaf card with little visible text requires nested detail, a smaller footprint, or an explicit QA exemption.
- Use `qa-primary`, `qa-support`, `qa-metadata`, and `qa-legend` tags on major regions. Use `qa-primary-flow`, `qa-response-flow`, `qa-data-flow`, and `qa-error-flow` on connectors. Use `qa-sequence:<track>` on event badges. Use `qa-background` only for a page-sized export-forcing rectangle that must be ignored by geometry QA.
- Reuse official or verified platform icons. Keep custom business logic as compact labeled components.
- Keep title, layer rails, and legend when they are part of the chosen reference grammar; keep them visually subordinate and proportional.
- Use restrained high-contrast outlines over white or pale fills. Favor compact technical cards and readable density over oversized icon panels.
- Use official logos for known services and frameworks. Internal processing cards may remain text-led.
- Embed verified logo data so the editable source renders without a network connection. When no exact official icon exists, use a neutral family icon or labeled generic representation rather than a misleading adjacent product logo.
- Verify formulas, timeout variants, framework names, security headers, data exposure, transaction boundaries, and response ownership directly from the selected source snapshot.
- If the user supplies a reference diagram, match it directly and do not introduce ImageGen art direction. Use ImageGen only when visual direction is absent.
- Run the matching `drawio_qa.py --diagram-type` profile, fix every error, resolve actionable warnings, export with embedded XML, and inspect the rendered artifact at 100% plus connector terminals at 200%.
