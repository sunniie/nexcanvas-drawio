# Unified command-line interface

The `nexcanvas` command is the supported automation surface for the technical
preview. Phase 3 adds a resumable orchestrator without changing persisted source,
lock, diagram, or asset schema version `2.0`, or the editable Draw.io delivery
format.

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
| `init` | Create the standard project directories and v2 contracts |
| `analyze capture` | Pin Git origin, revision, and tracked-file evidence |
| `analyze verify` | Reverify repository evidence against a local checkout |
| `plan` | Compare and score layout candidates |
| `build` | Compile a diagram model to native, uncompressed Draw.io XML |
| `render` | Export PNG, SVG, or PDF through Draw.io Desktop |
| `qa diagram` | Run contract, semantic, asset, connector, and geometry gates |
| `qa visual` | Record render checks and explicit human visual approval |
| `postflight` | Verify final hashes, provenance, and delivery gates |
| `generate` | Run or resume the hash-bound plan-to-postflight pipeline |
| `intent` | Infer a semantic view intent as an agent routing hint |
| `contract` | Validate a persisted v2 content contract or v1 pipeline-state contract |
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

## Compatibility

The `python scripts/*.py` interfaces published in `v0.1.x` remain as thin
source-checkout wrappers during the technical preview. New automation must use
the unified CLI. The wrappers are not installed into wheels and may be removed
only after the documented deprecation window.

The importable modules under `src/nexcanvas` are implementation details; the
technical preview does not yet publish a stable Python API.

## Known limits

- Draw.io Desktop remains required for deterministic raster/vector export and
  completed visual approval.
- Package installation does not install an Agent Skills host integration; hosts
  still discover `SKILL.md` through their own supported skill directory.
- Semantic authoring and visual judgment remain agent/human responsibilities;
  `generate` orchestrates deterministic stages but does not invent architecture
  facts or automatically approve aesthetics.
