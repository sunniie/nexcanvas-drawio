# Collaborative Intake and Discovery

Use this reference before drawing a new workflow, architecture, integration, or system-flow artifact. The goal is to prevent unsupported autonomous layout decisions without making a well-specified user repeat themselves.

## Gate 1: choose the artifact and language

First inventory what the conversation already answers. Ask only for unresolved high-impact choices.

If the workflow mode is not explicit, display both bundled examples before asking:

- `../assets/examples/architecture-overview.png` — a high-level capability and dependency map for README, portfolio, presentation, and system communication.
- `../assets/examples/detailed-request-flow.png` — an implementation-level interaction view with independent tracks, event order, authority, data access, fallbacks, and response behavior.

Use a local image-view tool so the user sees the previews in the conversation. If that tool is unavailable, provide clickable file paths plus the descriptions above.

Ask one compact round, normally no more than three questions:

1. **Artifact:** Architecture Overview, Detailed Request Flow, or both?
2. **Language:** match the user's language, English, Vietnamese, or bilingual?
3. **Audience and use:** README/presentation/portfolio, product discussion, or engineering/debugging? Ask for the repository, document, or source description only if none is available.

Ask output format and canvas together with question 3 when relevant. Default repository documentation output to editable `.drawio` plus `.drawio.png` with embedded XML.

Do not ask Gate 1 again when the user has already named the mode, language, audience, source, and output. If only one field is missing, ask only that field.

## Investigate before proposing boxes

Inspect available code, documents, diagrams, screenshots, and prior decisions. Separate confirmed facts from assumptions. Build a private inventory of:

- actors and entry points;
- real ownership, execution, trust, and network boundaries;
- capabilities or request events;
- state authorities, stores, queues, and external dependencies;
- responses, downstream consumers, fallbacks, and errors;
- official technologies versus internal/custom concepts.

Do not start with a target number of parts, columns, lanes, or badges.

## Gate 2: confirm the content model

Before writing XML, present a concise diagram brief in the chosen language:

```text
Purpose / audience:
Source snapshot:
Proposed structure:
- zones or interaction tracks, with why each boundary exists
- components inside each zone
Primary flow:
- capability relationship for Overview, or true events per track for Detailed
- response/callback owner and direction for every externally visible interaction
Dependencies and authority:
Icon plan:
- official logos: ...
- neutral task glyphs: ...
Output:
Assumptions / exclusions:
```

Make the proposal content-specific. Examples are visual grammar only; their five capabilities, three tracks, and event counts are never reusable defaults.

Pause for confirmation when changing any of these would materially change the artifact: scope boundary, workflow mode, interaction split, authority, included failure behavior, or language. If the user explicitly requests autonomous execution, show the brief as a decision record and continue.

## Derive composition from content

Choose the layout only after Gate 2:

- Use the smallest number of meaningful zones that explains ownership or execution.
- Size cards from information density and semantic importance.
- Distribute peer components across the usable width; do not inflate sparse cards to fill a preset grid.
- Create a new track only for a genuinely separate request, local action, background job, or state transition.
- Number only real events after the interaction ledger is stable.
- Reduce or expand the canvas when the content requires it; 1920x1080 is a documentation default, not a structural constraint.

## Plan icons deliberately

Use three icon tiers:

1. **Official resource logo:** verified service, framework, platform, database, cloud product, or observability tool. Embed it in the source.
2. **Neutral Draw.io semantic glyph:** task or internal concept such as user, browser, document, upload, OCR, shield/check, decision, review, transform, scoring, analytics, search, database, queue, notification, or output. Use a built-in General/Flowchart/Clipart/library shape or a small composed vector.
3. **Text-led component:** abstract business rule or dense internal logic where a glyph would add noise.

Never make a semantic glyph look like an official vendor mark. Keep glyph color aligned with the owning stage, and tag multi-shape compositions with `qa-illustrative` when needed by QA.

## Gate 3: verify semantics before review-ready export

After automated geometry QA, create a compact edge ledger for every primary, response, callback, retry, feedback, and authority-changing connector:

```text
source -> target | meaning | line class | authority/result owner
```

Trace the rendered arrowhead, not only the XML source/target fields. Reject any connector whose label describes the opposite direction. Represent request/response, delivery/acknowledgement, attempt/retry, and review/feedback as separate one-way edges when both directions matter.

Only call an artifact review-ready after the mode-specific QA profile is clean, the semantic edge ledger is consistent, and the PNG has been inspected at 100% plus connector terminals at 200%. A preliminary content draft must be labeled as such.

## Conversation behavior

- Explain why a question changes the diagram rather than asking a generic questionnaire.
- Prefer two short decision gates over a long form.
- Do not hide major assumptions inside the finished artifact.
- Treat user references as visual authority after content accuracy.
- If the user changes direction after Gate 2, update the brief before drawing instead of patching an incompatible layout.
