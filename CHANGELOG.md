# Changelog

All notable changes to NexCanvas are documented in this file. Releases follow
[Semantic Versioning](https://semver.org/), while persisted schemas are versioned
independently.

## [0.4.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.3.0...v0.4.0) (2026-09-10)


### Features

* **schema:** introduce canonical semantic model v3 ([#13](https://github.com/sunniie/nexcanvas-drawio/issues/13)) ([4e20be1](https://github.com/sunniie/nexcanvas-drawio/commit/4e20be1c2f5e1ff6aebb6454b6c767f8bf8a748a))

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
