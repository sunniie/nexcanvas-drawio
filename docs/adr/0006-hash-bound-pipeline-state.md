# ADR 0006: Hash-bound pipeline state

Status: Accepted for Phase 3 implementation

## Context

The Phase 2 commands are deterministic in isolation, but an agent still has to
remember their order and decide whether an existing report is current. That makes
resume behavior host-dependent and allows stale build, render, or approval files
to be mistaken for a completed delivery.

## Decision

NexCanvas will persist `project_state.json` at the project root. The file records
the ordered generate stages, each stage's canonical input hash, dependency output
hashes, generated output hashes, status, attempt count, and failure detail.

Before every orchestrated run, NexCanvas reconciles those records with the files
on disk. A changed input, dependency, option, missing output, or changed output
marks that stage stale and invalidates every downstream stage. Passing stages
whose inputs and outputs still match are reused. Failed and stale stages are safe
to retry without deleting project content.

The orchestrated `generate` command owns these stages:

1. layout planning;
2. editable Draw.io build;
3. diagram QA;
4. Draw.io render;
5. explicit visual approval;
6. postflight delivery verification.

Visual approval remains a real review boundary. A render can reach
`awaiting-review`, but the project cannot become `complete` until a reviewer
explicitly approves the current render and postflight passes. Machine-readable
results distinguish completed, awaiting-review, failed-gate, and invalid-input
outcomes.

## Public contract impact

- `project_state.json` and its JSON schema become public preview contracts.
- `nexcanvas generate` and its exit code `3` for an incomplete external review
  gate become public preview CLI contracts.
- Existing v2 source, lock, model, asset, and Draw.io contracts remain unchanged.
- Existing projects are migratable in place: the first `generate` run creates
  state from the files already present and revalidates rather than trusting them.

## Consequences

The same project can resume consistently across agent hosts and process failures.
Manual edits to generated outputs are detected as drift. Timestamp fields remain
informational; cache decisions depend only on canonical hashes and declared stage
dependencies.
