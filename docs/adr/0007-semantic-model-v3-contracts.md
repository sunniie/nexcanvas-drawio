# ADR 0007: Split Semantic Model V3 into canonical layers

- Status: accepted
- Date: 2026-09-10

## Context

The version 2 diagram model mixes architectural meaning with canvas choices.
Node identity, labels, evidence references, icon selection, coordinates, and
connector routing all live in the same records. A layout-only edit therefore
looks like a semantic change, and repository synchronization cannot preserve
manual presentation work without understanding renderer-specific fields.

## Decision

`diagram_model.json` schema `3.0` is the canonical diagram contract. It contains
three explicit layers:

- `metadata` records the view purpose and delivery context;
- `semantics` records stable groups, entities, relationships, and their
  fact-level provenance;
- `presentation` records theme, canvas, grouping placement, visual treatment,
  asset selection, geometry, connector lanes, labels, and routes.

The evidence corpus remains in `source_model.json`. Every V3 provenance entry
names a source fact and records the confidence used when the semantic assertion
was accepted. Generated Draw.io XML, previews, and QA reports remain outside the
canonical model under `artifacts/` and `reports/`.

Stable semantic IDs are user-visible public contracts. Presentation records
refer to those IDs and cannot redefine them. Changing coordinates, styles, icon
choices, or connector routes must not change the semantic fingerprint.

The compiler normalizes V3 into an internal renderer projection. That projection
is not persisted as a new source of truth. Draw.io metadata binds the generated
artifact to both the complete canonical-model hash and the semantics-only hash.

## Compatibility and migration

NexCanvas `v0.4.x` reads both diagram model `2.0` and `3.0`. New projects use
`3.0`; existing V2 projects continue to build without migration for at least the
`v0.4.x` compatibility window.

The `nexcanvas migrate v2-to-v3` command writes a separate V3 file, refuses to
overwrite by default, preserves existing node, edge, and boundary IDs, and moves
all geometry and rendering fields into the presentation layer. When a sibling or
explicit `source_model.json` is available, migration copies each referenced
fact's confidence into its provenance entry; unresolved confidence is recorded
as `unknown`, never guessed.

Migration is deterministic: the same V2 model and source evidence produce the
same V3 JSON and semantic fingerprint. Migration never rewrites the input file.

## Public-contract impact

- Adds diagram model schema `3.0` while retaining read compatibility with `2.0`.
- Adds `nexcanvas migrate v2-to-v3` and machine-readable migration output.
- Makes stable semantic IDs and the semantics-only fingerprint public preview
  contracts.
- Changes `nexcanvas init` to create V3 diagram models.
- Does not change `source_model.json`, `diagram_lock.json`, asset-manifest, or
  pipeline-state schema versions.

## Consequences

Semantic comparison can ignore presentation-only changes, and later repository
sync can reconcile facts without destroying manually curated layout. The
temporary cost is dual-version validation and normalization until V2 support is
retired through the documented deprecation policy.
