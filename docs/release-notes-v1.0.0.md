# NexCanvas v1.0.0 release notes

NexCanvas `v1.0.0` turns the technical-preview toolchain into a supportable
contract set for agents, contributors, and automation. The release does not
replace the visual grammar established by the reference diagrams; it makes the
interfaces around that workflow explicit, inspectable, portable, and testable.

## Highlights

- Stable public CLI command tree, options, UTF-8 JSON results, and exit codes.
- Machine-readable contract and platform registry in
  `config/stability-manifest.json`.
- `nexcanvas compatibility report` for the installed runtime and contract set.
- Read-only `nexcanvas compatibility check <project>` with actionable V2
  migration guidance and unknown-major rejection.
- Stable schemas and CLI validation for diagram QA, visual QA, and postflight
  reports.
- Fresh-wheel structural E2E coverage outside the repository:
  `init -> plan -> build -> diagram QA -> compatibility check`.
- Published compatibility, support, migration, rollback, deprecation, and
  security-response policies.

## Fixes

- Package the policy documents referenced by the stability manifest so installed
  wheels work independently of the source checkout.
- Normalize Diagram Model V3 before resolving the geometry-QA route in
  `nexcanvas qa diagram --drawio`. This fixes a V2-shaped route lookup that could
  fail after otherwise successful V3 validation.
- Make package-smoke failures include the failed command, stdout, and stderr.

## Compatibility

- Python 3.10 through 3.13 is supported. CI exercises every version on Ubuntu and
  Python 3.12 on Windows and macOS.
- Diagram Model V3 remains canonical.
- Diagram Model V2 remains readable, validatable, buildable, and explicitly
  migratable throughout the `1.x` line. Repository synchronization still
  requires V3.
- Existing Source Model, Diagram Lock, Asset Manifest, pipeline, repository,
  conformance, extension, and benchmark schema versions are unchanged.
- Extension manifest/API/protocol `1.0` and visual benchmark contracts `1.0`
  graduate from public preview to stable.
- Internal `src/nexcanvas` imports are not a stable Python API. The supported
  automation surface is the `nexcanvas` CLI.

## Known limits

- Draw.io Desktop remains required for deterministic PNG/SVG/PDF rendering and a
  completed visual-approval gate.
- Repository analysis remains static and module-oriented; it cannot prove
  runtime wiring or deployed infrastructure absent from evidence.
- Semantic authoring and visual judgment remain agent/human responsibilities.
- Cross-agent adapters and deterministic conformance evaluation are available,
  but Codex/Copilot/Claude equivalence is not claimed until current observed
  execution records exist for the required corpus.
- GitHub Releases, not a public package index, remain the authoritative binary
  distribution channel.
