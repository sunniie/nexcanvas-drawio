# Changelog

All notable changes to NexCanvas are documented in this file. Releases follow
[Semantic Versioning](https://semver.org/), while persisted schemas are versioned
independently.

## [0.3.0](https://github.com/sunniie/nexcanvas-drawio/compare/v0.2.0...v0.3.0) (2026-09-09)


### Features

* **pipeline:** add deterministic generate orchestration ([#10](https://github.com/sunniie/nexcanvas-drawio/issues/10)) ([38fb08b](https://github.com/sunniie/nexcanvas-drawio/commit/38fb08b07f2aaddea00fc6478f00136414b18bd4))

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
