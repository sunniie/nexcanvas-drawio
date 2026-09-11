# Extension authoring

NexCanvas extension manifest `1.0` lets contributors add behavior without
editing compiler modules. Extensions are explicit, versioned, and opt-in. They
do not replace built-in components.

## Trust boundary

Only load an extension you trust. Analyzer, layout, and QA components execute a
local command with the extension directory as its working directory. NexCanvas
uses `shell=False`, a bounded timeout, JSON stdin/stdout, and response
validation, but this is process fault isolation rather than a security sandbox.
An extension can exercise the same local authority as another developer tool.

NexCanvas never discovers extensions by scanning the current repository, home
directory, Python environment, or network. Every extension directory must be
passed explicitly with `--extension`.

## Directory contract

```text
my-extension/
|-- nexcanvas-extension.json
|-- hook.py
|-- route.json
|-- provider.json
`-- host.json
```

Validate before use:

```bash
nexcanvas extension validate ./my-extension
```

The command returns a machine-readable inventory containing the manifest hash,
declared-file hashes, a clone-path-independent content fingerprint, extension
version, component IDs, and execution mode. Duplicate component IDs,
path traversal, missing resources, incompatible API versions, and malformed
commands fail before a hook runs.

## Manifest

```json
{
  "schemaVersion": "1.0",
  "apiVersion": "1.0",
  "id": "com.example.diagram-tools",
  "name": "Example diagram tools",
  "version": "1.0.0",
  "requiresNexCanvas": ">=0.5.0,<0.8.0",
  "components": [
    {
      "kind": "analyzer",
      "id": "golang",
      "protocolVersion": "1.0",
      "fileSuffixes": [".go"],
      "command": ["{python}", "hook.py"]
    },
    {"kind": "route", "id": "service-map", "source": "route.json"}
  ]
}
```

`{python}` resolves to the interpreter running NexCanvas. Relative Python or
executable arguments are confined to the extension root. Commands are argument
arrays; shell strings are rejected.

## Component contracts

| Kind | Mode | Pipeline boundary |
|---|---|---|
| `analyzer` | JSON hook | Parses declared file suffixes during revision-pinned repository analysis |
| `layout` | JSON hook | Returns complete node, boundary, and edge geometry for its layout ID |
| `route` | JSON resource | Adds one family/profile route and its notation, layout, QA profile, and compatible intents |
| `asset-provider` | JSON resource | Adds one provider icon-pack definition used by `asset sync` |
| `qa-rule` | JSON hook | Appends typed error, warning, or info issues after core QA |
| `host-adapter` | JSON resource | Adds one data-only host descriptor to conformance discovery and run preparation |

Built-in IDs and file suffixes are reserved. An extension cannot shadow them.

### Hook envelope

NexCanvas sends one object on stdin:

```json
{
  "protocolVersion": "1.0",
  "kind": "qa-rule",
  "componentId": "policy-check",
  "request": {}
}
```

The hook must write exactly one JSON object to stdout:

```json
{
  "protocolVersion": "1.0",
  "ok": true,
  "result": {}
}
```

Diagnostics belong on stderr. Non-zero exits, timeout, extra stdout, unknown
protocol versions, and malformed results fail the calling command.

Analyzer results contain `symbols`, `imports`, and `diagnostics` arrays. Layout
results contain complete `nodes`, `boundaries`, and `edges` maps; every model ID
must appear exactly once and all geometry must be finite. QA results contain an
`issues` array with `severity`, `code`, `message`, and optional `location`.

## Testing an extension

Keep extension tests isolated from user repositories. The complete fixture at
[`tests/fixtures/extensions/complete`](../tests/fixtures/extensions/complete)
demonstrates all six component kinds and runs each hook as a subprocess. Tests
should cover at least:

- manifest and API compatibility;
- duplicate ID and path-traversal rejection;
- deterministic output for identical input;
- timeout, non-zero exit, and malformed response handling;
- complete layout ID coverage and finite geometry;
- analyzer ambiguity without destructive semantic deletion; and
- QA severity and location validation.

Use an extension on supported commands by repeating `--extension` when needed:

```bash
nexcanvas init ./project --name "Service map" --family custom --profile service-map --extension ./my-extension
nexcanvas analyze snapshot ./repo --extension ./my-extension
nexcanvas build diagram_model.json -o diagram.drawio --extension ./my-extension
nexcanvas qa diagram diagram_model.json --drawio diagram.drawio --extension ./my-extension
nexcanvas generate ./project --extension ./my-extension
nexcanvas sync ./project --repo-root ./repo --dry-run --extension ./my-extension
nexcanvas postflight ./project --extension ./my-extension
nexcanvas contract diagram-model ./project/diagram_model.json --extension ./my-extension
```

Pass the same extension set on every command that handles an extension-backed
project. NexCanvas deliberately does not persist executable extension paths in
the project. During `generate`, the manifest and all declared hook/resource
files participate in stage fingerprints; changed extension content invalidates
the build and downstream approvals instead of silently reusing stale output.
