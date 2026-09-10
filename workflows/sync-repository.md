# Synchronize a repository-backed diagram

Use this workflow when an existing Diagram Model V3 project must follow a newer
Git revision without discarding manual semantic or presentation edits.

## 1. Establish the sync boundary

Read [../references/semantic-intents-and-repository-evidence.md](../references/semantic-intents-and-repository-evidence.md)
and confirm the existing diagram still answers the intended question. Repository
analysis is module-level evidence, not permission to add every discovered file to
the communicated architecture. Narrow the analyzer with repeated `--include` or
`--exclude` patterns when the repository is larger than the diagram scope.

Incremental sync requires `diagram_model.json` schema `3.0`. Migrate a V2 model
non-destructively and review the candidate before continuing.

## 2. Preview the source change

Run the non-mutating plan first:

```bash
nexcanvas sync <project-dir> --repo-root <repo-root> --dry-run
```

The first run has an empty analyzer baseline and therefore proposes additions.
Later runs compare `repository_snapshot.json` with a new revision-aware snapshot.
Read the result as a three-way plan:

- `operations` are safe source-only additions or updates;
- `conflicts` mean the repository and current model changed the same field;
- `pendingRemovals` are never deleted implicitly;
- `diff` is the analyzer-level semantic change between revisions;
- `diagnostics` identify syntax or resolution uncertainty that must not be
  promoted into invented facts.

Dry-run does not modify project files. Supplying `--output` is an explicit request
to persist a copy of the plan at that path.

## 3. Review identity and manual work

Check stable IDs before applying. Git-detected file renames should retain the old
module ID. Verify that additions are in scope, and trace every proposed removal
back to its exact file and revision.

Current user values win a field conflict. Existing presentation records remain
untouched, including assets, importance, boundaries, coordinates, label
placement, ports, connector lanes, rails, and custom waypoints. A newly added
semantic record receives only a minimal presentation record so the normal layout
planner can place it later.

## 4. Apply conservatively

Apply safe changes:

```bash
nexcanvas sync <project-dir> --repo-root <repo-root> --apply
```

If removal is intended, pass each reviewed stable ID explicitly:

```bash
nexcanvas sync <project-dir> --repo-root <repo-root> --apply \
  --confirm-removal <semantic-id> \
  --confirm-removal <relationship-id>
```

An incomplete apply may still write safe additions and updates while retaining
conflicts and unconfirmed removals. It writes the incoming source state to
`reports/repository_snapshot.candidate.json` and leaves the applied baseline
unchanged. Resolve semantic conflicts in `diagram_model.json`, then rerun dry-run.
Only a complete reconciliation advances `repository_snapshot.json`.

Applied sync updates analyzer-owned facts and sources in `source_model.json`,
refreshes `diagram_lock.json.sourceHash`, and writes
`reports/semantic_sync.json`. It does not rebuild Draw.io output.

## 5. Rebuild and verify

Run the ordinary generation pipeline with the same repository root:

```bash
nexcanvas generate <project-dir> --repo-root <repo-root>
```

Inspect the current preview. Confirm that preserved positions and connector lanes
still communicate the intended story and that new nodes have been integrated
deliberately. Approve only the artifact actually viewed, then complete postflight.

## Static analyzer boundary

Phase 5 supports Git-tracked Python, TypeScript, JavaScript, TSX, JSX, MTS, CTS,
MJS, and CJS files. It extracts modules, public top-level symbols, and statically
resolvable internal imports. It does not claim dynamic runtime calls, framework
routes, generated code behavior, ownership, deployment, or production topology.
Those meanings require separate evidence and agent judgment.
