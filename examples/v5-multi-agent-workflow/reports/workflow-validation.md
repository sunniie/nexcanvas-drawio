# Brief-first workflow validation

Date: 2026-09-06

## Corrected behavior

The repository intake and installed Codex drawio entrypoint begin with the user's
brief and diagram language. They now also preserve any visual reference or named
standard established earlier in the conversation. Removing the old style menu does
not permit the agent to reset the design to its default theme.

## End-to-end case

The multi-agent case was rebuilt from the approved full brief rather than the small
pipeline smoke test. The final model contains 16 nodes, 15 relationships, five
lifecycle phases, two nested specialist groups, a bounded retry loop, human
escalation, a task-state authority, and a foundation band for tools, durable memory,
and telemetry.

Its dominant semantic intent is now recorded explicitly as `workflow`. The
`agent-orchestration` profile supplies the specialized notation, while the intent
contract ensures that QA traces the executable path, step order, branch convergence,
retry loop, and terminal outcomes instead of treating the drawing as a generic
architecture inventory.

The selected visual archetype is `provider-neutral-reference` with the Microsoft
reference theme. It transfers the supplied examples' phase columns, pale gray
backgrounds, flat service icons, neutral orthogonal connectors, green numbered
handoffs, nested execution groups, and foundation band. Generic MIT-licensed vector
icons are embedded because the architecture names no Azure product; they do not
pretend to be Microsoft service logos.

Layout brainstorming selected `hybrid-grid` over `dense-phase-columns` because
the request includes parallel branches and a retry cycle. The visible result retains
a left-to-right Microsoft-style phase composition and uses a dedicated lower feedback
rail.

## Validation performed

- Strict semantic and geometry QA: zero errors and zero warnings.
- All 11 generic SVG assets embedded into the editable Draw.io artifact.
- Draw.io Desktop PNG export inspected at original size.
- Primary flow, parallel branches, retry rail, human escalation, and terminal
  attachments traced visually.
- Icon-led node envelopes are now enforced after kind, description, asset, grid,
  and manual sizing. The `Human approval` and `User receives result` captions were
  re-rendered below their icons with visible clearance.
- Contract and layout regression tests cover both an undersized explicit model
  override and a constrained grid cell, preventing the same overlap from returning
  in another route.
- Package tests, geometry tests, skill metadata validation, visual approval, and
  postflight run after the final model change.
- The editable Draw.io root metadata, diagram model, and lock agree on
  `viewIntent=workflow`.

## Conversation walkthrough

| Input | Required action |
| --- | --- |
| Brief and language resolved | Proceed and derive internal design choices |
| Language absent | Ask only for diagram language |
| Material content ambiguity | Ask one focused content question |
| Microsoft examples already supplied | Preserve their visual grammar in later work |
| Explicit new visual reference | Replace the prior visual authority |
| Prior implementation approval | Continue without another routine confirmation |

No fresh GitHub Copilot or Claude session was executed. The checks cover the local
instruction behavior and complete model-build-render-QA pipeline.

## Cleanup retained

Four obsolete intake/style documents, three unused preset PNGs, three unreferenced
legacy Draw.io examples, and the retired pixel-offset label branch were removed.
The old `general / overview / detailed` selector was also replaced by internal
`baseline / composition / interaction` geometry profiles; users are never asked to
pick one. New projects no longer create empty icon directories or title chrome.
Active geometry QA, route semantics, reference projects, and user outputs remain in
place.
