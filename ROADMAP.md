# NexCanvas roadmap

This file is the canonical implementation checklist for NexCanvas. A phase is a
milestone, not a long-lived branch. Work is delivered through short-lived pull
request branches and is marked complete only after its exit gates pass.

## Status

- [x] Phase 0 - scope and architecture decisions
- [x] Phase 1 - open-source foundation
- [x] Phase 2 - installable package and unified CLI
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

Exit evidence:

- [x] [Pull request #1](https://github.com/sunniie/nexcanvas-drawio/pull/1)
  was squash-merged after its cross-platform quality gate passed.
- [x] The [post-merge CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34307965262)
  passed on Linux, Windows, and macOS.
- [x] `main` requires pull requests and the `Quality gate`, enforces linear
  history and resolved conversations, and blocks force pushes and deletion.
- [x] Automatic head-branch deletion and private vulnerability reporting are enabled.
- [x] GitHub Release [`v0.1.0`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.1.0)
  is the checksummed technical-preview baseline.

## Phase 2 - installable package and unified CLI

Objective: run NexCanvas predictably from any working directory and supported
agent host.

- [x] Add `pyproject.toml` and a `src/nexcanvas` package.
- [x] Provide the `nexcanvas` entry point.
- [x] Consolidate doctor, init, analyze, plan, build, render, QA, and postflight.
- [x] Resolve configuration and assets independently of the current directory.
- [x] Test editable installs and packaged installs on all supported platforms.

Implementation evidence:

- [`docs/cli.md`](docs/cli.md) records commands, exit codes, package behavior,
  compatibility, and known limits.
- [`scripts/package_smoke.py`](scripts/package_smoke.py) builds a wheel, installs
  it in an isolated environment, and exercises it outside the repository.
- The CI matrix performs editable installation, the full regression suite, and
  packaged-install smoke testing on Linux, Windows, and macOS.

Exit evidence:

- [Pull request #7](https://github.com/sunniie/nexcanvas-drawio/pull/7)
  introduced the installable package and unified CLI after the cross-platform
  [Quality gate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34324481526)
  passed.
- [Release pull request #8](https://github.com/sunniie/nexcanvas-drawio/pull/8)
  passed its final [Linux, Windows, and macOS package matrix](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34324936404).
- The post-merge [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34325077514)
  passed without bypassing the required gate.
- GitHub Release [`v0.2.0`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.2.0)
  publishes the portable skill bundle, wheel, source distribution, and verified
  SHA-256 checksums.
- Persisted schema version remains `2.0`; existing generated projects require no
  migration.

Target release: `v0.2.0`.

## Phase 3 - deterministic pipeline

Objective: make workflow gates executable rather than prompt-dependent.

Recorded scope and contract impact:

- [`ADR 0006`](docs/adr/0006-hash-bound-pipeline-state.md) defines the ordered
  stage graph, hash reconciliation, downstream invalidation, safe resume, and the
  non-bypassable visual-review boundary.
- `project_state.json`, `nexcanvas generate`, and exit code `3` are new public
  preview contracts. Existing schema `2.0` project inputs remain valid and gain
  state on their first orchestrated run; no source-model migration is required.

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
