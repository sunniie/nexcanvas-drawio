# NexCanvas v0.7.0 release notes

NexCanvas v0.7.0 adds a versioned extension ecosystem and a release-grade
visual benchmark framework while preserving editable Draw.io output and the
existing Diagram Model V2/V3 contracts.

## Features

- Explicit, versioned extensions for analyzers, layouts, routes, asset
  providers, QA rules, and host adapters.
- A bounded JSON subprocess protocol for executable hooks and data-only
  registry components for declarative extensions.
- A seven-class visual benchmark corpus covering sparse, dense, cloud, AI,
  sequence, data-flow, and lifecycle diagrams.
- Release-grade benchmark results combining contracts, geometry, text bounds,
  deterministic PNG proxies, and hash-current human review.

## Fixes

- Sequence messages use independent horizontal lifeline routes in request order.
- Explicit node coordinates support intentional cyclic/state compositions.
- Geometry QA no longer treats flow labels or semantic state shapes as missing
  technology icons.
- Extension content participates in resumable pipeline invalidation.

## Compatibility

- Diagram Model V2 and V3 remain supported with no migration.
- Extensions are opt-in and are never auto-discovered or persisted as executable
  paths in generated projects.
- New extension and visual benchmark schemas are public preview at version `1.0`.

## Known limits

- Executable extensions are trusted local code; subprocess isolation is not a
  security sandbox.
- PNG metrics detect broken or implausible renders, not aesthetic quality;
  release approval still requires visual inspection.
- Phase 6 observed cross-host comparison remains open as an independent roadmap
  item. This does not change the Phase 7 extension or benchmark contracts and
  no cross-host equivalence is claimed by this release.
