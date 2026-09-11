# Unified command-line interface

The `nexcanvas` command is the supported automation surface for the technical
preview. Product `v0.6.x` creates canonical diagram model `3.0`, reads legacy
diagram model `2.0`, and keeps source, lock, asset, pipeline-state, and editable
Draw.io contracts at their existing versions. Repository sync requires V3.

## Installation

From a cloned repository:

```bash
python -m pip install -e .
```

From an unpacked release bundle:

```bash
python -m pip install .
```

GitHub releases also attach a wheel and source distribution with checksums. A
public package-index publication is not claimed in the technical preview.

The wheel installs its immutable registries, schemas, and pinned generic icon
catalog under the Python installation's data directory. Project outputs always
remain relative to the caller's working directory unless an explicit project
path is supplied.

For agent hosts that clone a skill but cannot install a package, this launcher
exposes the identical parser and behavior:

```bash
python <skill-root>/scripts/nexcanvas_cli.py <command> [...]
```

## Commands

| Command | Responsibility |
|---|---|
| `doctor` | Inspect Python, Node, Draw.io, and authoring capabilities |
| `init` | Create the standard project directories and a canonical V3 diagram model |
| `analyze capture` | Pin Git origin, revision, and tracked-file evidence |
| `analyze verify` | Reverify repository evidence against a local checkout |
| `analyze snapshot` | Extract revision-pinned Python and TypeScript/JavaScript module semantics |
| `analyze diff` | Compare two repository snapshots by stable semantic ID |
| `plan` | Compare and score layout candidates |
| `build` | Compile a diagram model to native, uncompressed Draw.io XML |
| `render` | Export PNG, SVG, or PDF through Draw.io Desktop |
| `qa diagram` | Run contract, semantic, asset, connector, and geometry gates |
| `qa visual` | Record render checks and explicit human visual approval |
| `postflight` | Verify final hashes, provenance, and delivery gates |
| `generate` | Run or resume the hash-bound plan-to-postflight pipeline |
| `sync` | Preview or apply a conservative three-way repository semantic reconciliation |
| `migrate v2-to-v3` | Write a separate canonical V3 model from a legacy V2 model |
| `intent` | Infer a semantic view intent as an agent routing hint |
| `contract` | Validate a persisted V2/V3 diagram contract or another supported contract |
| `conformance doctor` | Detect locally available host adapters without claiming a passing run |
| `conformance prepare` | Create a host/case run pack bound to the skill, adapter, and corpus digests |
| `conformance evaluate` | Score a fixture or observed project across the five conformance dimensions |
| `conformance report` | Aggregate observed results into a truthful host capability matrix |
| `asset search` | Search the pinned technology icon catalog |
| `asset sync` | Resolve a verified catalog, provider, or user-owned SVG asset |

Use `nexcanvas <command> --help` for command-specific options.

## Output and exit codes

Normal command results are UTF-8 JSON on standard output. `--help` and
`--version` are intentionally human-readable. Runtime and input failures are a
compact JSON object on standard error.

| Exit | Meaning |
|---:|---|
| `0` | Command completed and its requested gate passed |
| `1` | A validation, QA, postflight, or search result did not pass |
| `2` | Invalid usage/input, unavailable required runtime, or manual asset resolution required |
| `3` | Generation reached the external visual-review gate and is not complete yet |

Callers must inspect both the exit code and persisted report rather than parsing
display wording. `generate` also emits `outcome`, `complete`, `currentStage`, and
an ordered `events` array whose actions are `ran`, `reused`, `invalidated`, or
`failed`.

## Orchestrated generation

After the agent has confirmed the source and lock, authored the diagram model,
and resolved required assets, run:

```bash
nexcanvas generate <project-dir> [--repo-root <repo-root>]
```

The first passing run normally exits `3` after writing the preview and a pending
visual report. Inspect that exact artifact, then resume:

```bash
nexcanvas generate <project-dir> [--repo-root <repo-root>] \
  --approve-visual \
  --reviewer "<reviewer>" \
  --notes "<specific observations from the rendered image>"
```

Approval requires both reviewer and notes. The second run reuses matching stages,
binds approval to the current preview hash, and executes postflight. `--restart`
invalidates all stage records without deleting source or generated files.
`--allow-warnings` relaxes the default release behavior and must not be used to
silently hide an actionable warning.

State is persisted at `<project-dir>/project_state.json`. See
[deterministic pipeline state](pipeline-state.md) for invalidation and recovery
semantics.

## V2-to-V3 migration

Migration never rewrites its input and refuses an existing output unless
`--force` is explicit:

```bash
nexcanvas migrate v2-to-v3 <v2-model> --output <v3-model> [--source-model <source-model>]
```

When `--source-model` is omitted, a sibling `source_model.json` is used if
present. The JSON result reports counts and a semantics-only fingerprint. The
new file must pass `contract diagram-model`, build, render, visual QA, and
postflight before replacing a project's active model. See the
[Semantic Model V3 reference](../references/semantic-model-v3.md).

## Repository analysis and semantic sync

Create a standalone analyzer snapshot:

```bash
nexcanvas analyze snapshot <repo-root> --output repository_snapshot.json
nexcanvas analyze snapshot <repo-root> --previous repository_snapshot.json \
  --output repository_snapshot.next.json
nexcanvas analyze diff repository_snapshot.json repository_snapshot.next.json
```

The optional previous snapshot enables Git rename-aware stable IDs. Analysis is
limited to tracked Python and TypeScript/JavaScript-family files and the pinned
`HEAD`; dirty working-tree content is not silently analyzed. Repeat `--include`
or `--exclude` to define a smaller scope, and use `--max-files` as an explicit
repository-size guard.

For a Diagram Model V3 project, always preview synchronization first:

```bash
nexcanvas sync <project-dir> --repo-root <repo-root> --dry-run
nexcanvas sync <project-dir> --repo-root <repo-root> --apply
```

`--dry-run` does not modify the project unless `--output` explicitly requests a
saved plan. Apply writes safe additions and source-only updates, preserves
current values for same-field conflicts, and never removes a semantic record
without a repeated `--confirm-removal <stable-id>` option. Existing presentation
records are retained at the record level; new semantics receive minimal
presentation records for later layout.

A complete apply advances `<project>/repository_snapshot.json`. If conflicts or
unconfirmed removals remain, the source candidate is written to
`reports/repository_snapshot.candidate.json` while the applied baseline stays
unchanged. Every apply writes `reports/semantic_sync.json`, updates analyzer facts
in `source_model.json`, and refreshes `diagram_lock.json.sourceHash`. Run
`generate --repo-root` afterwards to rebuild and visually verify the artifact.

## Cross-agent conformance

Prepare a run pack from the bundled five-intent corpus:

```bash
nexcanvas conformance doctor
nexcanvas conformance prepare <case-id> --host <host-id> --output <run-pack>
```

After the named host completes the generated `PROMPT.md`, retain its transcript,
fill `execution.json`, and evaluate the untouched project:

```bash
nexcanvas conformance evaluate <run-pack>/request.json \
  --project <run-pack>/project \
  --mode observed \
  --execution <run-pack>/execution.json \
  --output <run-pack>/result.json
```

`--mode fixture` is reserved for evaluator tests and always emits status
`fixture`, even when every dimension passes. `conformance report` ignores fixture
results when determining host status. See [cross-agent conformance](conformance.md).

## Extensions

Validate one or more explicitly trusted extension roots:

```bash
nexcanvas extension validate ./my-extension [./another-extension]
```

Commands that expose an extension boundary accept repeatable `--extension`
options. The option is local to the subcommand and must appear after that
subcommand's arguments:

```bash
nexcanvas init ./project --name "Service map" --family custom --profile service-map --extension ./my-extension
nexcanvas analyze snapshot ./repo --extension ./my-extension
nexcanvas build diagram_model.json -o diagram.drawio --extension ./my-extension
nexcanvas qa diagram diagram_model.json --drawio diagram.drawio --extension ./my-extension
nexcanvas generate ./project --extension ./my-extension
nexcanvas sync ./project --repo-root ./repo --dry-run --extension ./my-extension
nexcanvas postflight ./project --extension ./my-extension
nexcanvas contract diagram-model ./project/diagram_model.json --extension ./my-extension
nexcanvas asset sync ./project service-name --provider custom-pack --extension ./my-extension
nexcanvas conformance doctor --extension ./my-extension
```

Invalid manifests, incompatible API ranges, duplicate IDs, path traversal,
hook timeout, process failure, and malformed responses return exit code `2`.
Executable hooks are trusted local developer tools, not sandboxed code. See
[extension authoring](extensions.md).

Extension paths are never discovered or persisted. Repeat the same explicit
set for each command. `generate` fingerprints the extension manifest and all
declared files, so changed hook or resource content invalidates stale pipeline
stages and visual approval.

## Visual benchmarks

```bash
nexcanvas benchmark validate
nexcanvas benchmark run [--output benchmark-result.json]
nexcanvas benchmark run --automated-only
```

The release profile exits `0` only when all seven cases pass geometry,
text-bound, PNG-proxy, and current hash-bound human-review gates.
`--automated-only` exits `0` when automated checks pass but always emits
`passed: false`; it cannot establish aesthetic approval. See
[visual benchmarks](visual-benchmarks.md).

## Compatibility

The `python scripts/*.py` interfaces published in `v0.1.x` remain as thin
source-checkout wrappers during the technical preview. New automation must use
the unified CLI. The wrappers are not installed into wheels and may be removed
only after the documented deprecation window.

The importable modules under `src/nexcanvas` are implementation details; the
technical preview does not yet publish a stable Python API.

Diagram model `2.0` remains readable throughout `v0.6.x`. New `init` output uses
diagram model `3.0`; source model and diagram lock remain schema `2.0`, while
pipeline state, repository snapshot, and semantic sync plan use independent
schema `1.0` contracts. Incremental sync requires V3.

## Known limits

- Draw.io Desktop remains required for deterministic raster/vector export and
  completed visual approval.
- Package installation does not install an Agent Skills host integration; hosts
  still discover `SKILL.md` through their own supported skill directory.
- Semantic authoring and visual judgment remain agent/human responsibilities;
  `generate` orchestrates deterministic stages but does not invent architecture
  facts or automatically approve aesthetics.
- The `v0.6.x` pipeline fingerprints the complete diagram-model file, so a
  presentation-only edit conservatively reruns every delivery stage even though
  its semantics-only fingerprint remains stable.
- Phase 5 analyzers expose module/import evidence only. They do not infer dynamic
  runtime calls, framework routing, ownership, deployment, or production state.
- A bundled adapter and local executable detection do not prove host conformance.
  Only complete, current observed corpus runs can produce `verified` status.
