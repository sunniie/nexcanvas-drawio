# NexCanvas roadmap

This file is the canonical implementation checklist for NexCanvas. A phase is a
milestone, not a long-lived branch. Work is delivered through short-lived pull
request branches and is marked complete only after its exit gates pass.

## Status

- [x] Phase 0 - scope and architecture decisions
- [x] Phase 1 - open-source foundation
- [x] Phase 2 - installable package and unified CLI
- [x] Phase 3 - deterministic pipeline state and orchestration
- [x] Phase 4 - canonical semantic model V3
- [x] Phase 5 - repository analysis and incremental semantic sync
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

- [x] Add hash-bound `project_state.json` stage records.
- [x] Invalidate downstream stages when inputs change.
- [x] Support safe resume after failures.
- [x] Prevent completion while render or visual QA remains pending.
- [x] Provide one orchestrated generate command with machine-readable output.

Implementation evidence:

- [`docs/pipeline-state.md`](docs/pipeline-state.md) documents stage inputs,
  output reconciliation, invalidation, exit codes, visual review, and recovery.
- [`tests/test_pipeline.py`](tests/test_pipeline.py) covers pending review,
  approval, full reuse, model drift, output tampering, failed-stage resume, false
  completion rejection, and the CLI JSON result.
- Packaged-install smoke validates that the wheel exposes `generate` and creates
  a valid state contract outside the repository.

Exit evidence:

- [Pull request #10](https://github.com/sunniie/nexcanvas-drawio/pull/10)
  introduced the pipeline after the Linux, Windows, and macOS
  [Quality gate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34328465148)
  passed.
- The post-merge feature [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34328573800)
  and final release [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34328961700)
  both passed.
- [Release pull request #11](https://github.com/sunniie/nexcanvas-drawio/pull/11)
  passed its complete cross-platform package matrix before merge.
- GitHub Release [`v0.3.0`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.3.0)
  publishes the portable skill bundle, wheel, source distribution, and verified
  SHA-256 checksums with feature, fix, compatibility, and known-limit notes.
- The released wheel was installed in an isolated environment outside the
  repository; `doctor`, `init`, and `contract project-state` passed, and the
  release tag matched the final main commit.
- A real Draw.io run completed `generate → awaiting-review → inspected PNG →
  approval/postflight → full reuse`; the temporary smoke project was removed.

Existing v2 content contracts remain unchanged. The new pipeline state uses its
independent public preview schema `1.0`; existing projects gain it on first
orchestrated use without a source-model migration.

Target release: `v0.3.0`.

## Phase 4 - canonical semantic model V3

Objective: separate evidence, semantics, presentation, and generated artifacts.

Recorded scope and contract impact:

- [`ADR 0007`](docs/adr/0007-semantic-model-v3-contracts.md) defines the V3
  metadata, semantics, and presentation layers; stable-ID and provenance
  invariants; the non-destructive migration contract; and the V2 compatibility
  window.
- Diagram model `3.0`, `nexcanvas migrate v2-to-v3`, and the semantics-only
  fingerprint are new public preview contracts. Diagram model `2.0` remains
  readable throughout `v0.4.x`; the other persisted contract versions do not
  change.

- [x] Introduce stable semantic entity and relationship IDs.
- [x] Record confidence and provenance per fact.
- [x] Move coordinates, style, and connector routes into a presentation layer.
- [x] Provide V2-to-V3 migrations and compatibility tests.

Implementation evidence:

- [`schemas/diagram-model-v3.schema.json`](schemas/diagram-model-v3.schema.json)
  and [`references/semantic-model-v3.md`](references/semantic-model-v3.md)
  define the canonical layer, stable-ID, provenance, and presentation-reference
  contracts.
- [`src/nexcanvas/model_v3.py`](src/nexcanvas/model_v3.py) implements
  deterministic V2 normalization, non-destructive migration, and semantic
  fingerprints that ignore presentation-only changes.
- [`tests/test_model_v3.py`](tests/test_model_v3.py) covers migration fidelity,
  overwrite safety, provenance, stable IDs, presentation ownership and coverage,
  confidence drift, fingerprint stability, CLI behavior, and Draw.io bindings.
- Builder, planner, quality, postflight, package-smoke, and pipeline paths accept
  V3 while preserving V2 readability; new `init` projects use V3 by default.

Exit evidence:

- [Pull request #13](https://github.com/sunniie/nexcanvas-drawio/pull/13)
  introduced V3 after its Linux, Windows, macOS, validator, reference-postflight,
  and [Quality gate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34444342291)
  passed.
- [Release pull request #14](https://github.com/sunniie/nexcanvas-drawio/pull/14)
  documented features, fixes, compatibility, and known limits and passed its
  complete
  [cross-platform package matrix](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34444769821).
- The feature [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34444590114)
  and final release [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34444881747)
  passed all required jobs.
- GitHub Release [`v0.4.0`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.4.0)
  publishes the portable skill bundle, wheel, source distribution, and matching
  SHA-256 checksums with full release notes.
- The published wheel was installed outside the repository: version, `doctor`,
  V3 `init`, diagram-model contract validation, and migration help passed. The
  portable ZIP contains the V3 schema, migration module, reference, and skill.
- A migrated reference project completed a real Draw.io Desktop cycle through
  generation, rendered PNG inspection, explicit approval, zero-error postflight,
  and deterministic full-stage reuse. All four tracked V2 reference projects
  continue to pass live postflight validation.
- Diagram Model V2 remains readable for the complete `v0.4.x` line; migration is
  opt-in, does not modify its input, and preserves stable IDs and extension data.

Phase gate evaluation:

- [x] Scope and public-contract impact were recorded in ADR 0007 before
  implementation.
- [x] Design, implementation, release, and completion evidence used reviewable
  commits and short-lived branches.
- [x] New V3 behavior has migration, contract, compiler, pipeline, and CLI coverage.
- [x] Existing unit and Draw.io QA suites pass.
- [x] The repository-local and Agent Skill validators pass.
- [x] All tracked reference projects pass live postflight validation.
- [x] Published wheel and portable ZIP checks pass outside the repository.
- [x] User-visible behavior and migration requirements are documented.
- [x] Feature, release, and final-main CI runs are green.
- [x] Release notes cover features, fixes, compatibility, and known limits.

Target release: `v0.4.0` (released 2026-09-10).

## Phase 5 - repository analysis and semantic sync

Objective: update diagrams as repositories evolve without destroying manual work.

Recorded scope and contract impact:

- [`ADR 0008`](docs/adr/0008-repository-snapshot-and-three-way-sync.md) defines
  revision-pinned Python and TypeScript/JavaScript analysis, repository snapshot
  `1.0`, semantic sync-plan `1.0`, conservative removals, and field-level
  three-way reconciliation.
- `analyze snapshot`, `analyze diff`, `sync --dry-run`, and `sync --apply` are new
  public-preview CLI contracts. Incremental sync requires Diagram Model V3; all
  existing persisted contract versions remain unchanged.

- [x] Implement Python and TypeScript/JavaScript analyzers first.
- [x] Add snapshot, semantic diff, and `sync --dry-run`.
- [x] Implement three-way reconciliation of old semantics, new source, and edits.
- [x] Preserve stable IDs, annotations, positions, and unaffected connector lanes.
- [x] Never delete low-confidence or ambiguous entities without confirmation.

Implementation evidence:

- [`src/nexcanvas/repository_analysis.py`](src/nexcanvas/repository_analysis.py)
  extracts revision-pinned modules, public symbols, and internal static imports,
  preserves IDs across Git-detected renames, and retains last-known semantics as
  `unknown` when parsing becomes ambiguous.
- [`src/nexcanvas/semantic_sync.py`](src/nexcanvas/semantic_sync.py) implements
  field-level three-way reconciliation, explicit removal confirmation,
  presentation preservation, source-fact refresh, candidate snapshots, and lock
  hash updates.
- [`schemas/repository-snapshot.schema.json`](schemas/repository-snapshot.schema.json)
  and [`schemas/semantic-sync-plan.schema.json`](schemas/semantic-sync-plan.schema.json)
  define the new independently versioned `1.0` contracts.
- [`tests/test_repository_sync.py`](tests/test_repository_sync.py) covers mixed
  Python/TypeScript/JavaScript analysis, rename identity, parser ambiguity,
  fingerprint tampering, CLI snapshot/diff/contracts, non-mutating dry-run,
  three-way conflict handling, manual geometry/annotation/lane preservation,
  conservative removals, evidence verification, and V2 rejection.
- [`workflows/sync-repository.md`](workflows/sync-repository.md) and
  [`docs/cli.md`](docs/cli.md) document the portable Agent Skill and CLI flow.

Exit evidence:

- [Pull request #16](https://github.com/sunniie/nexcanvas-drawio/pull/16)
  introduced repository analysis and semantic synchronization after its full
  [cross-platform Quality gate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34456149519)
  passed. The post-merge
  [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34456284978)
  passed the same gate.
- GitHub prereleases
  [`v0.5.0-alpha.1`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.5.0-alpha.1)
  and [`v0.5.0-rc.1`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.5.0-rc.1)
  were built from short-lived release branches after their respective
  [alpha](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34456764602)
  and [release-candidate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34457504933)
  matrices passed on Linux, Windows, and macOS.
- [Pull request #18](https://github.com/sunniie/nexcanvas-drawio/pull/18)
  removed deprecated package metadata discovered by the alpha build; its
  [Quality gate](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34457167661)
  and post-merge
  [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34457309768)
  passed before the release candidate was cut.
- [Release pull request #17](https://github.com/sunniie/nexcanvas-drawio/pull/17)
  records features, fixes, compatibility, and known limitations and passed its
  [complete release matrix](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34457954570).
  The final release
  [main CI run](https://github.com/sunniie/nexcanvas-drawio/actions/runs/34458139545)
  also passed every required job.
- GitHub Release [`v0.5.0`](https://github.com/sunniie/nexcanvas-drawio/releases/tag/v0.5.0)
  publishes the portable skill bundle, wheel, source distribution, and matching
  SHA-256 checksums. The published wheel was installed outside the repository;
  version `0.5.0`, full-tier `doctor`, sync command discovery, and both packaged
  sync schemas were verified.
- Release Please was rerun after the stable tag and produced no spurious release
  proposal, confirming that the next release cycle starts after `v0.5.0`.

Phase gate evaluation:

- [x] Scope and public-contract impact were recorded in ADR 0008 before
  implementation.
- [x] Design, implementation, packaging repair, prereleases, and completion
  evidence used reviewable commits and short-lived branches.
- [x] New analyzer and reconciliation behavior has repository, contract, CLI,
  conflict, preservation, removal-safety, and compatibility coverage.
- [x] All 75 unit tests and 25 Draw.io QA regression tests pass.
- [x] The repository-local and Agent Skill validators pass.
- [x] All four tracked reference projects pass live postflight validation.
- [x] Published wheel and portable ZIP checks pass outside the repository.
- [x] User-visible behavior, V3 requirements, and known limits are documented.
- [x] Feature, alpha, release-candidate, release, and final-main CI runs are green.
- [x] Release notes cover features, fixes, compatibility, and known limits.

Target release: `v0.5.0` (released 2026-09-10), preceded by alpha and
release-candidate builds.

## Phase 6 - cross-agent conformance

Objective: measure consistent semantics and quality across Codex, Copilot, Claude,
and compatible Agent Skills hosts.

- [x] Keep one shared core and thin host-specific adapters.
- [x] Build a representative conformance corpus.
- [ ] Compare semantic coverage, evidence, assets, routing, and gate completion.
- [x] Publish a host capability and limitation matrix.

Target release: `v0.6.0`.

Accepted scope: one shared `SKILL.md` and CLI core; data-only host adapters;
versioned, provider-neutral corpus cases; deterministic artifact scoring across
five independent dimensions; and a capability matrix that distinguishes
`verified`, `not-run`, `unavailable`, and `failed`. Fixture runs may test the
evaluator but may not establish host support. See ADR 0009.

Implementation checkpoint: the suite contains five semantic-intent cases and two
tracked fixture baselines; four data-only host adapters share the root skill; the
installed wheel carries the corpus, adapters, schemas, and skill digest input;
and CI validates the scorer plus the rule that fixtures cannot verify a host.
Observed corpus runs are still required before the comparison item and Phase 6
can be marked complete.

## Phase 7 - extension ecosystem and visual benchmarks

Objective: let contributors extend the project without editing compiler internals.

Recorded scope and contract impact:

- [`ADR 0010`](docs/adr/0010-versioned-extensions-and-visual-benchmarks.md)
  defines explicit extension loading, component and protocol versioning,
  executable-hook trust boundaries, real pipeline integration, and hash-bound
  visual benchmark dimensions.
- Extension manifest `1.0`, extension protocol `1.0`, benchmark suite `1.0`, and
  benchmark result `1.0` are new public-preview contracts. Extensions remain
  opt-in, so existing projects and Diagram Model V2/V3 require no migration.

- [x] Version analyzer, layout, route, asset-provider, QA-rule, and host adapters.
- [x] Add an extension authoring guide and isolated plugin tests.
- [x] Build sparse, dense, cloud, AI, sequence, data-flow, and lifecycle benchmarks.
- [x] Combine geometry, perceptual, text-bound, and human visual review gates.

Implementation checkpoint: all six extension kinds enter their real runtime
boundaries through an explicit `--extension` option; extension manifests,
declared hooks, and resources are hash-bound to resumable generation; isolated
fixtures cover loading, confinement, routing, layout, QA, analysis, project
initialization, and invalidation. The seven-class benchmark corpus has editable
Draw.io files, rendered PNGs, zero geometry/text-bound findings, deterministic
perceptual checks, and hash-current human approvals. Phase 7 remains unreleased
until the `v0.6.0` release line is closed, the Phase 7 feature PR passes final
CI, and the normal `v0.7.0` release gates complete.

Target releases: `v0.7.x`.

## Phase 8 - stable contracts and 1.0 hardening

Objective: publish a supportable public API and migration promise.

- [ ] Stabilize CLI and contract schemas.
- [ ] Verify fresh installation and end-to-end examples on supported platforms.
- [ ] Resolve critical issues and publish the compatibility matrix.
- [ ] Document support, migration, rollback, and security-response policies.
- [ ] Publish immutable, checksummed `v1.0.0` artifacts.

Target release: `v1.0.0`.
