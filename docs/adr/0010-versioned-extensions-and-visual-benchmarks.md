# ADR 0010: Versioned extensions and visual benchmarks

- Status: accepted
- Date: 2026-09-11
- Decision owners: NexCanvas maintainers

## Context

NexCanvas currently keeps repository analyzers, layout strategies, route
profiles, provider icon packs, QA rules, and host adapters in separate internal
registries. Contributors must edit compiler modules or distribution-owned data
to add behavior. That couples extensions to implementation details and makes it
hard to test compatibility independently.

The project also has polished reference examples but no repeatable benchmark
contract that distinguishes structural correctness, rendered-image checks,
text clearance, and human visual judgment. A valid Draw.io file is not by itself
evidence that a diagram is readable or visually intentional.

## Decision

### One explicit extension contract

NexCanvas will introduce extension manifest schema `1.0` and extension protocol
`1.0`. A manifest declares an extension ID, its own version, compatible
NexCanvas API range, and one or more independently versioned components:

- analyzer;
- layout;
- route;
- asset-provider;
- QA-rule; and
- host-adapter.

Extensions are loaded only from paths explicitly supplied by the caller. There
is no implicit scan of the current repository, user profile, Python environment,
or network. Duplicate component IDs fail deterministically. Resource paths are
resolved beneath the extension root; path traversal and missing files fail
before execution.

Route, asset-provider, and host-adapter components are data resources validated
against their public contracts. Analyzer, layout, and QA-rule components may use
an executable JSON protocol when declarative data is insufficient. Commands are
argument arrays, never shell strings. NexCanvas sends one JSON request on stdin,
expects one JSON object on stdout, applies a bounded timeout, and validates the
response before using it.

Executable hooks are fault-isolated processes, not a security sandbox. Loading
one grants trusted local-code authority equivalent to running another developer
tool. Documentation must state this boundary plainly.

### Integration, not registration-only support

Each component participates in its real pipeline boundary:

- analyzers augment revision-pinned repository snapshots;
- layouts return validated node, boundary, and connector geometry;
- routes participate in route resolution and contract validation;
- asset providers participate in provider-pack resolution;
- QA rules append typed issues to the standard quality report; and
- host adapters participate in conformance discovery and run preparation.

The CLI will provide extension validation and inspection, plus explicit
extension options on commands that execute extension behavior. Core behavior is
unchanged when no extension is supplied.

### A hash-bound visual benchmark suite

Benchmark suite and result schema `1.0` will cover seven visual classes:
sparse, dense, cloud, AI, sequence, data-flow, and lifecycle. Each case binds a
source model, expected intent and density, render settings, and required gates.

Automated benchmark results keep four dimensions separate:

1. geometry: node overlap, connector collision, and routing checks;
2. perceptual proxies: render existence, dimensions, ink coverage, and visual
   entropy or equivalent deterministic image statistics;
3. text bounds: labels, badges, captions, and icon-safe text clearance; and
4. human review: an explicit reviewer decision bound to the rendered artifact
   hash and the required visual criteria.

Automated perceptual proxies must not be described as aesthetic approval.
Missing or stale human review leaves a case pending and prevents a release-grade
benchmark pass. CI may run an automated-only profile, but that status is reported
as such and cannot satisfy the human gate.

## Compatibility and versioning

Extension and benchmark schemas are public-preview contracts in `v0.7.x` and
version independently from the product. Unknown major versions fail with an
actionable error. Existing projects and Diagram Model V2/V3 remain readable;
extensions are opt-in and introduce no migration.

The extension API compatibility range is evaluated against the supported API
level, not against private Python module names. Breaking a published extension
protocol requires a new protocol major and a documented transition path.

## Consequences

- Contributors can add supported behavior without modifying compiler internals.
- Extension loading remains deterministic and auditable across agent hosts.
- Third-party executable hooks require an explicit trust decision.
- Benchmarks make visual regressions measurable while preserving the required
  human judgment boundary.
- Phase 7 cannot be marked complete from XML validation, fixtures, or automated
  image proxies alone; real renders must be inspected and hash-bound approvals
  must be current.

