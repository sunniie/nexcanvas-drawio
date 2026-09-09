# Unified command-line interface

The `nexcanvas` command is the supported automation surface for the Phase 2
technical preview. It replaces the collection of task-specific scripts without
changing persisted schema version `2.0` or the editable Draw.io delivery format.

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
| `intent` | Infer a semantic view intent as an agent routing hint |
| `contract` | Validate one persisted v2 contract |
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

Callers must inspect both the exit code and persisted report rather than parsing
display wording.

## Compatibility

The `python scripts/*.py` interfaces published in `v0.1.x` remain as thin
source-checkout wrappers for the `v0.2.x` line. New automation must use the
unified CLI. The wrappers are not installed into wheels and may be removed only
after the documented deprecation window.

The importable modules under `src/nexcanvas` are implementation details; Phase 2
does not yet publish a stable Python API.

## Known limits

- Draw.io Desktop remains required for deterministic raster/vector export and
  completed visual approval.
- Package installation does not install an Agent Skills host integration; hosts
  still discover `SKILL.md` through their own supported skill directory.
- Phase 2 does not orchestrate the complete pipeline automatically. Executable
  stage state and safe resume belong to Phase 3.
