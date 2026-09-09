# Public contracts

NexCanvas versions the interfaces that users, agents, generated projects, and
extensions depend on. Before `v1.0.0`, these contracts may change, but breaking
changes require release notes and a migration path whenever persisted user data is
affected.

## Versioned surfaces

The following are public contracts:

- documented command names, options, exit codes, and machine-readable output;
- `source_model.json`, semantic/diagram model, and `diagram_lock.json` schemas;
- asset-manifest and QA-report schemas;
- the standard generated-project directory layout;
- stable semantic IDs once Semantic Model V3 is introduced;
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
