# NexCanvas roadmap

This file is the canonical implementation checklist for NexCanvas. A phase is a
milestone, not a long-lived branch. Work is delivered through short-lived pull
request branches and is marked complete only after its exit gates pass.

## Status

- [x] Phase 0 - scope and architecture decisions
- [ ] Phase 1 - open-source foundation (in progress until GitHub exit gates pass)
- [ ] Phase 2 - installable package and unified CLI
- [ ] Phase 3 - deterministic pipeline state and orchestration
- [ ] Phase 4 - canonical semantic model V3
- [ ] Phase 5 - repository analysis and incremental semantic sync
- [ ] Phase 6 - cross-agent conformance
- [ ] Phase 7 - extension ecosystem and visual benchmarks
- [ ] Phase 8 - stable contracts and 1.0 hardening

## Mandatory phase gate

Every phase must satisfy this checklist before its status changes to complete.

- [ ] Scope and public-contract impact are recorded before implementation.
- [ ] Work is split into reviewable, short-lived branches.
- [ ] New behavior has meaningful tests or fixtures.
- [ ] Existing unit and Draw.io QA suites pass.
- [ ] `python scripts/validate_skill.py` passes.
- [ ] Reference projects pass live postflight validation.
- [ ] A clean-clone or equivalent portability check passes.
- [ ] User-visible changes and migration needs are documented.
- [ ] CI is green on the final commit.
- [ ] Release notes describe features, fixes, compatibility, and known limits.

The checklist above is reset and evaluated for each phase. Completion evidence
belongs in the phase section and in the corresponding pull request or release.

## Phase 0 - scope and architecture decisions

Objective: define what NexCanvas promises before expanding implementation.

- [x] Define the mission, supported use cases, and explicit non-goals.
- [x] Separate agent judgment from deterministic compiler responsibilities.
- [x] Declare versioned public contracts and stability expectations.
- [x] Separate product, schema, asset-pack, and artifact versions.
- [x] Record the repository-sync and editable-output architecture decisions.

Evidence:

- [`docs/project-scope.md`](docs/project-scope.md)
- [`docs/public-contracts.md`](docs/public-contracts.md)
- [`docs/versioning.md`](docs/versioning.md)
- [`docs/adr/`](docs/adr/)

## Phase 1 - open-source foundation

Objective: make the project safe to change, test, release, and contribute to.

- [x] Add contribution, conduct, security, and support policies.
- [x] Add issue forms, pull-request template, and code ownership.
- [x] Add cross-platform Python and reference-project CI.
- [x] Add a repository-local skill/package validator.
- [x] Adopt short-lived branches and Conventional Commit pull-request titles.
- [x] Configure automated release pull requests and changelog generation.
- [x] Define the initial `v0.1.0` technical-preview release.
- [x] Document required repository rules for `main`.

Exit evidence required on GitHub:

- The `CI / Quality gate` status is green.
- `main` requires pull requests and the quality gate, and blocks force pushes.
- Private vulnerability reporting is enabled.
- GitHub Release `v0.1.0` contains a source bundle and SHA-256 checksum.

## Phase 2 - installable package and unified CLI

Objective: run NexCanvas predictably from any working directory and supported
agent host.

- [ ] Add `pyproject.toml` and a `src/nexcanvas` package.
- [ ] Provide the `nexcanvas` entry point.
- [ ] Consolidate doctor, init, analyze, plan, build, render, QA, and postflight.
- [ ] Resolve configuration and assets independently of the current directory.
- [ ] Test editable installs and packaged installs on all supported platforms.

Target release: `v0.2.0`.

## Phase 3 - deterministic pipeline

Objective: make workflow gates executable rather than prompt-dependent.

- [ ] Add hash-bound `project_state.json` stage records.
- [ ] Invalidate downstream stages when inputs change.
- [ ] Support safe resume after failures.
- [ ] Prevent completion while render or visual QA remains pending.
- [ ] Provide one orchestrated generate command with machine-readable output.

Target release: `v0.3.0`.

## Phase 4 - canonical semantic model V3

Objective: separate evidence, semantics, presentation, and generated artifacts.

- [ ] Introduce stable semantic entity and relationship IDs.
- [ ] Record confidence and provenance per fact.
- [ ] Move coordinates, style, and connector routes into a presentation layer.
- [ ] Provide V2-to-V3 migrations and compatibility tests.

Target release: `v0.4.0`.

## Phase 5 - repository analysis and semantic sync

Objective: update diagrams as repositories evolve without destroying manual work.

- [ ] Implement Python and TypeScript/JavaScript analyzers first.
- [ ] Add snapshot, semantic diff, and `sync --dry-run`.
- [ ] Implement three-way reconciliation of old semantics, new source, and edits.
- [ ] Preserve stable IDs, annotations, positions, and unaffected connector lanes.
- [ ] Never delete low-confidence or ambiguous entities without confirmation.

Target release: `v0.5.0`, preceded by alpha and release-candidate builds.

## Phase 6 - cross-agent conformance

Objective: measure consistent semantics and quality across Codex, Copilot, Claude,
and compatible Agent Skills hosts.

- [ ] Keep one shared core and thin host-specific adapters.
- [ ] Build a representative conformance corpus.
- [ ] Compare semantic coverage, evidence, assets, routing, and gate completion.
- [ ] Publish a host capability and limitation matrix.

Target release: `v0.6.0`.

## Phase 7 - extension ecosystem and visual benchmarks

Objective: let contributors extend the project without editing compiler internals.

- [ ] Version analyzer, layout, route, asset-provider, QA-rule, and host adapters.
- [ ] Add an extension authoring guide and isolated plugin tests.
- [ ] Build sparse, dense, cloud, AI, sequence, data-flow, and lifecycle benchmarks.
- [ ] Combine geometry, perceptual, text-bound, and human visual review gates.

Target releases: `v0.7.x`.

## Phase 8 - stable contracts and 1.0 hardening

Objective: publish a supportable public API and migration promise.

- [ ] Stabilize CLI and contract schemas.
- [ ] Verify fresh installation and end-to-end examples on supported platforms.
- [ ] Resolve critical issues and publish the compatibility matrix.
- [ ] Document support, migration, rollback, and security-response policies.
- [ ] Publish immutable, checksummed `v1.0.0` artifacts.

Target release: `v1.0.0`.
