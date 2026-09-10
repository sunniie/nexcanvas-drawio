# Public contracts

NexCanvas versions the interfaces that users, agents, generated projects, and
extensions depend on. Before `v1.0.0`, these contracts may change, but breaking
changes require release notes and a migration path whenever persisted user data is
affected.

## Versioned surfaces

The following are public contracts:

- documented command names, options, exit codes, and machine-readable output;
- `source_model.json`, semantic/diagram model, `diagram_lock.json`, and
  `project_state.json` schemas;
- asset-manifest and QA-report schemas;
- the standard generated-project directory layout;
- stable semantic IDs and semantics-only fingerprints in diagram model V3;
- repository snapshot `1.0` and semantic sync-plan `1.0`;
- extension manifests and plugin interfaces once published;
- the delivery definition for editable, rendered, and verified artifacts.

The `nexcanvas` command and its documented subcommands are public preview
contracts. Python modules under `src/nexcanvas` remain implementation details
until a supported Python API is explicitly published.

## Compatibility classes

- **Backward compatible:** existing valid projects continue to build and validate.
- **Migratable:** an explicit migration command converts the old contract without
  silently discarding semantics or manual edits.
- **Breaking:** existing projects or automation require user changes. This must be
  called out prominently in release notes.

## Schema policy

Schema versions are independent of the NexCanvas product version. A product patch
may support multiple schema versions, while a schema-major change requires a
migration tool and fixtures covering representative prior projects.

Unknown schema-major versions must fail with an actionable message. They must not
be guessed, partially loaded, or silently rewritten.

Diagram model `3.0` is canonical from product `v0.4.0`. Diagram model `2.0`
remains a readable compatibility contract throughout `v0.5.x`, and the explicit
V2-to-V3 migration writes a separate output instead of silently replacing user
data.

Repository snapshot and semantic sync-plan schema `1.0` are introduced in
product `v0.5.0`. They do not change Diagram Model V3, Source Model `2.0`,
Diagram Lock `2.0`, or pipeline-state `1.0`. Incremental sync is rejected for V2
models rather than guessing how to preserve mixed semantic/presentation fields.

## Deprecation policy

Before `v1.0.0`, a deprecated contract is documented in the changelog and retained
for at least one subsequent minor release when practical. After `v1.0.0`, supported
contracts receive at least one minor-release deprecation window before removal,
except for urgent security fixes.

## Agent-host contract

Host-specific skill discovery and permissions are separate from the diagram
contract. A host is supported only when its documented installation is tested and
its capability limitations are published. Prompt similarity alone is not evidence
of cross-agent conformance.
