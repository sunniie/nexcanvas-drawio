# Compatibility matrix

This document is the human-readable view of the NexCanvas `1.0` public contract
set. The packaged machine-readable source is
[`config/stability-manifest.json`](../config/stability-manifest.json).

## Supported runtime matrix

| Runtime | Supported versions | Required CI coverage |
|---|---|---|
| Python | 3.10, 3.11, 3.12, 3.13 | Ubuntu on every version; Windows and macOS on 3.12 |
| Ubuntu | current `ubuntu-latest` GitHub-hosted image | Unit, Draw.io QA, wheel install, contract and benchmark gates |
| Windows | current `windows-latest` GitHub-hosted image | Unit, Draw.io QA and wheel installation |
| macOS | current `macos-latest` GitHub-hosted image | Unit, Draw.io QA and wheel installation |

Python 3.12 is the reference release runtime. A platform is not removed from the
supported matrix in a patch release. Changes to this matrix are announced in
release notes and follow the deprecation policy.

Draw.io Desktop is an optional runtime dependency for authoring but is required
for deterministic PNG/SVG/PDF export and completed visual approval. A portable
runtime without Draw.io can still initialize, validate, plan, build native
editable `.drawio`, inspect compatibility, and run non-rendering contract gates.

## Stable persisted contracts

| Contract | Stable schema | `v1.x` behavior |
|---|---:|---|
| Diagram Model | `3.0` | Canonical read/write contract |
| Diagram Model legacy | `2.0` | Read/validate/build and non-destructive V2-to-V3 migration |
| Source Model | `2.0` | Stable read/write contract |
| Diagram Lock | `2.0` | Stable read/write contract |
| Asset Manifest | `2.0` | Stable read/write contract |
| Diagram, Visual, and Postflight QA | `2.0` | Stable generated report contracts |
| Pipeline State | `1.0` | Stable resumable-stage contract |
| Repository Snapshot and Sync Plan | `1.0` | Stable repository reconciliation contracts |
| Conformance contracts | `1.0` | Stable evaluator and observed-evidence contracts |
| Extension manifest/API/protocol | `1.0` | Stable explicit trusted-extension contracts |
| Visual benchmark suite/result | `1.0` | Stable release-grade visual gate contracts |

Schema versions are independent of the NexCanvas product version. Unknown major
versions fail with guidance rather than being guessed.

## Compatibility inspection

Inspect the installed contract set and runtime:

```bash
nexcanvas compatibility report
```

Check an existing project without modifying it:

```bash
nexcanvas compatibility check ./nexcanvas-output/my-project
```

Legacy Diagram Model V2 projects remain compatible, but the report recommends
the explicit non-destructive migration before repository synchronization:

```bash
nexcanvas migrate v2-to-v3 ./project/diagram_model.json \
  --output ./project/diagram_model.v3.json
```

## Not covered by the platform matrix

Agent-host skill discovery, permissions, model behavior, and UI tooling are not
equivalent to operating-system support. Refer to the
[host capability and conformance matrix](host-capability-matrix.md) for observed
host evidence. A prompt or successful local installation alone does not establish
cross-agent equivalence.
