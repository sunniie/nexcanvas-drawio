# ADR 0011: Stabilize the NexCanvas 1.0 contract set

Status: accepted for `v1.0.0`

## Context

NexCanvas already exposes a unified CLI, persisted project contracts, extension
and benchmark protocols, and a portable skill package. Those surfaces were
introduced as technical previews across the `0.x` releases. A stable release
needs one reviewable statement of what is supported, how compatibility is
measured, and which implementation details remain private.

Documentation alone is not sufficient. CLI drift, a missing packaged schema, or
an unsupported platform claim must fail CI before a release is published.

## Decision

`v1.0.0` establishes public contract set `1.0` with these boundaries:

- the documented `nexcanvas` command tree, options, JSON output, and exit codes
  are stable public automation interfaces;
- persisted schemas listed in `config/stability-manifest.json` are stable at
  their recorded versions and version independently from the product;
- Diagram Model V3 is canonical; Diagram Model V2 remains readable and
  explicitly migratable throughout the `1.x` product line;
- extension manifest/API/protocol `1.0`, conformance `1.0`, and visual benchmark
  `1.0` are stable public contracts;
- Python modules under `src/nexcanvas` remain implementation details. No stable
  import-level Python API is promised by `v1.0.0`;
- supported Python and operating-system combinations are the combinations
  listed in the stability manifest and exercised by the required CI matrix;
- agent-host discovery is not part of platform compatibility. A host receives a
  conformance claim only from a digest-bound observed execution.

The checked-in stability manifest is the machine-readable contract registry.
`nexcanvas compatibility report` exposes it from an installed package, while
`nexcanvas compatibility check <project>` validates a project without rewriting
it and provides migration guidance for legacy V2 models.

## Compatibility rules

- Patch releases do not remove or reinterpret a stable command, option, exit
  code, or persisted field.
- Minor releases may add optional commands, options, fields, and schema minors.
- Removing or changing an existing stable surface requires a major product or
  schema version, a documented migration, and a deprecation window of at least
  one minor release except for urgent security fixes.
- Unknown schema majors fail with an actionable error and are never guessed or
  silently rewritten.
- Migration writes a separate output by default. Rollback means retaining the
  pre-migration project and using a release that still supports its contract;
  generated artifacts alone are not a rollback source of truth.

## Release enforcement

CI validates the stability manifest, compares the live argparse tree with the
recorded CLI surface, verifies every registered schema is packaged, performs a
fresh wheel installation outside the repository, and runs the reference and
visual benchmark gates. `v1.0.0` release artifacts must include a skill bundle,
wheel, source distribution, and SHA-256 checksum file.

## Consequences

Contributors can extend NexCanvas without accidentally changing a stable public
surface. Intentional breaking changes carry more design and migration work. The
project continues to evolve its internal Python modules freely as long as the
stable external contracts remain compatible.
