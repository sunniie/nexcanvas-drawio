# Migration and rollback

NexCanvas treats persisted project contracts as user data. Migration is explicit,
non-destructive by default, and separate from generated Draw.io artifacts.

## Before changing a project

1. Record the NexCanvas version and run `nexcanvas compatibility check <project>`.
2. Commit or copy the complete project, including source/model/lock contracts,
   local assets, editable Draw.io, reports, and `project_state.json`.
3. Read the target release notes for schema, extension, and known-limit changes.
4. Run migration into a separate candidate path. Never use a rendered image as
   the only rollback source.

## Diagram Model V2 to V3

V2 remains readable, validatable, buildable, and explicitly migratable throughout
the `1.x` product line. Repository synchronization requires V3.

```bash
nexcanvas migrate v2-to-v3 ./project/diagram_model.json \
  --source-model ./project/source_model.json \
  --output ./project/diagram_model.v3.json
nexcanvas contract diagram-model ./project/diagram_model.v3.json
```

Build and visually verify the candidate before replacing the active model. The
migration preserves semantic IDs and does not overwrite its input. `--force`
applies only to the explicit output path.

## Rollback

If a migration or product upgrade cannot be accepted:

- restore the pre-change project snapshot;
- reinstall the previously verified wheel or skill bundle from its checksummed
  GitHub Release;
- run `nexcanvas compatibility check` and the relevant project postflight using
  that version;
- do not mix a newer `project_state.json` or generated report with older semantic
  contracts unless the compatibility report explicitly accepts it.

Stable patch releases do not require persisted-contract migration. A future
breaking schema release must ship a separate migration command, fixtures for the
supported prior contract, and release-specific rollback guidance.

## Extension rollback

Extensions are loaded only from explicitly supplied directories. Retain the exact
extension version and files used by a passing build. Removing `--extension` is a
safe diagnostic step, but a project that references extension-defined routes,
assets, analyzers, or QA rules cannot be regenerated without the compatible
extension. NexCanvas fingerprints declared extension files so stale approval is
invalidated rather than silently reused.
