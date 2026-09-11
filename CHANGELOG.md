# Changelog

All notable changes to NexCanvas are documented in this file. Releases follow
[Semantic Versioning](https://semver.org/), while persisted schemas are versioned
independently.

## [0.6.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.5.0...v0.6.0) (2026-09-11)


### Features

* **conformance:** add evidence-based host evaluation ([#23](https://github.com/sunniie/nexcanvas-drawio/issues/23)) ([50b2812](https://github.com/sunniie/nexcanvas-drawio/commit/50b281271261982ea4415c62905a9328427a3fe0))

## [0.5.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.4.0...v0.5.0) (2026-09-10)


### Features

* **sync:** add incremental repository reconciliation ([#16](https://github.com/sunniie/nexcanvas-drawio/issues/16)) ([a06b76c](https://github.com/sunniie/nexcanvas-drawio/commit/a06b76c959c40de170cca2eb4fd9401c59640ce7))

- Add Git-pinned repository snapshots for Python, TypeScript, JavaScript, and
  their JSX/module variants, including modules, public symbols, and static
  internal imports.
- Add `nexcanvas analyze snapshot`, `nexcanvas analyze diff`, and
  `nexcanvas sync` with schema-validated, machine-readable plans.
- Reconcile baseline, incoming repository facts, and the current V3 model with
  a field-level three-way merge that preserves manual presentation work.

### Fixes

* **packaging:** modernize license metadata ([#18](https://github.com/sunniie/nexcanvas-drawio/issues/18)) ([86a5ea6](https://github.com/sunniie/nexcanvas-drawio/commit/86a5ea6971bfdb6a70e4db1ada775003daae9aeb))

- Retain last-known semantics as `unknown` when a parser cannot safely resolve
  a changed source file; ambiguous evidence is never converted into deletion.
- Reject snapshots from unrelated repository origins and preserve stable IDs
  across Git-detected renames.
- Keep unresolved apply results in a candidate snapshot and clean that
  candidate only after a complete, confirmed synchronization.

### Compatibility

- Incremental synchronization requires Diagram Model V3. V2 projects remain
  readable and can be migrated explicitly with `nexcanvas migrate v2-to-v3`.
- Existing source, diagram-lock, asset-manifest, and project-state schema
  versions are unchanged. Repository Snapshot and Semantic Sync Plan begin at
  schema version `1.0`.
- Existing render, QA, repair, and reference-conversion workflows remain
  available without repository synchronization.

### Known limitations

- Repository analysis is static and module-oriented. It does not infer runtime
  wiring, framework dependency injection, infrastructure, or deployment
  topology that is not represented by supported source imports and symbols.
- The agent or author still chooses the correct architectural viewpoint and
  must review conflicts, pending removals, and semantic uncertainty.
- A successful semantic sync does not replace Draw.io rendering and visual
  inspection before delivery.

## [0.4.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.3.0...v0.4.0) (2026-09-10)


### Features

* **schema:** introduce canonical semantic model v3 ([#13](https://github.com/sunniie/nexcanvas-drawio/issues/13)) ([4e20be1](https://github.com/sunniie/nexcanvas-drawio/commit/4e20be1c2f5e1ff6aebb6454b6c767f8bf8a748a))

- Separate evidence, semantics, and presentation into explicit ownership layers
  with stable IDs and fact-level provenance.
- Add `nexcanvas migrate v2-to-v3` for deterministic, non-destructive project
  migration and make new projects use Diagram Model V3 by default.
- Bind editable Draw.io output to both the complete model fingerprint and the
  presentation-independent semantic fingerprint.

### Fixes

- Reject semantic/presentation field mixing, missing or duplicate presentation
  references, and confidence drift from the source evidence model.
- Prevent accidental in-place migration and output replacement unless the user
  explicitly supplies `--force`.

### Compatibility

- Diagram Model V2 remains readable throughout the `0.4.x` release line; an
  immediate migration is not required for existing projects.
- Source Model and Diagram Lock remain at schema `2.0`, while pipeline state
  remains at schema `1.0`.
- Migration preserves V2 semantic IDs and extension data and never modifies the
  input file.

### Known limitations

- Any change to `diagram_model.json` conservatively invalidates all generated
  pipeline stages; semantic-aware incremental synchronization is planned for
  Phase 5.
- V3 defines and validates the architecture contract but does not infer unknown
  repository architecture or replace required visual review.

## [0.3.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.2.0...v0.3.0) (2026-09-09)


### Features

* **pipeline:** add deterministic generate orchestration ([#10](https://github.com/sunniie/nexcanvas-drawio/issues/10)) ([38fb08b](https://github.com/sunniie/nexcanvas-drawio/commit/38fb08b07f2aaddea00fc6478f00136414b18bd4))

### Fixes

- Detect missing or externally changed generated outputs before reusing a stage.
- Avoid false invalidation when an unchanged asset advances from `Embedded` to
  `RenderVerified`.

### Compatibility

- Existing source, lock, diagram, asset, and editable Draw.io schema `2.0`
  projects remain valid; their first orchestrated run creates
  `project_state.json` in place.
- Pipeline state uses its own public preview schema `1.0`.
- `nexcanvas generate` adds exit code `3` for a successful handoff to required
  external visual review. Existing command exit codes are unchanged.

### Known limitations

- Semantic investigation, model authoring, and visual judgment remain agent or
  human responsibilities; orchestration does not infer unknown architecture.
- Draw.io Desktop and actual image inspection are still required for a completed
  visual gate.

## [0.2.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.1.0...v0.2.0) - 2026-09-09

### Added

- Installable `src/nexcanvas` Python package and `nexcanvas` console command.
- Unified doctor, init, analyze, plan, build, render, QA, postflight, contract,
  intent, and asset command groups.
- Working-directory-independent runtime data resolution for editable and wheel
  installs.
- Cross-platform editable-install and packaged-install smoke coverage.

### Changed

- Agent instructions and documentation now use the unified CLI.
- GitHub releases now build a wheel and source distribution in addition to the
  portable skill bundle.
- The v0.1 task-specific scripts remain as compatibility wrappers and are
  deprecated for new automation.

### Compatibility

- Persisted schema version remains `2.0`; existing projects require no migration.
- Draw.io output remains native, uncompressed, and editable.

### Known limitations

- Full pipeline orchestration and resumable stage state remain planned for Phase 3.
- Draw.io Desktop is still required for rendering and completed visual approval.

## [0.1.0] - 2026-09-09

### Added

- Portable Agent Skill workflows for generation, repair, and reference conversion.
- Evidence, diagram, lock, asset, render, visual-review, and postflight contracts.
- Five semantic intents, 48 technical profiles, and content-driven layout planning.
- Native editable Draw.io generation with embedded verified SVG assets.
- Connector, label, icon, boundary, route, and collision quality gates.
- Four complete editable reference projects, including a multi-agent workflow.
- Project scope, public-contract, versioning, contribution, security, and support
  policies.
- Cross-platform CI, repository-local validation, and automated release tooling.

### Known limitations

- The implementation is not yet distributed as an installable Python package.
- Repository evidence is pinned and verified but semantic repository updates are
  not yet reconciled incrementally.
- Cross-agent consistency has not yet been established by a published conformance
  suite.
- Visual approval requires Draw.io Desktop and an actual render inspection.

[0.1.0]: https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.1.0
