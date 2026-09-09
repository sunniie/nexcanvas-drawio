# Project contract

A v2 diagram project is a reproducible evidence-to-artifact workspace. When no
explicit project path is supplied, create it at
`<current-working-directory>/nexcanvas-output/<project-slug>/`. Never write a
user project into the installed skill directory.

```text
nexcanvas-output/<project-slug>/
|-- source_model.json
|-- diagram_lock.json
|-- diagram_model.json
|-- project_state.json
|-- assets/
|   |-- asset_manifest.json
|   `-- icons/
|-- artifacts/
|   |-- diagram.drawio
|   `-- diagram.drawio.png
`-- reports/
    |-- runtime.json
    |-- build.json
    |-- diagram_qa.json
    |-- render.json
    |-- visual_qa.json
    `-- postflight.json
```

## Source model

The source model is the evidence boundary. Facts should be atomic and reference exact files, symbols, document sections, screenshots, URLs, commits, or explicit user statements. `confidence=confirmed` means the cited source supports the claim; it does not mean the implementation was executed.

For repository-backed work, record the canonical Git origin and full commit hash on the repository source, then use structured fact evidence with repo-relative path and line range. Release QA reopens those paths from the pinned commit; a current working-tree file is not sufficient evidence. See [semantic intents and repository evidence](semantic-intents-and-repository-evidence.md).

## Diagram lock

The lock prevents silent design drift. It must record semantic view intent, route, notation, layout, audience, delivery target, theme, canvas, asset policy, and the canonical source hash. Use `draft` during exploration and `confirmed` for delivery.

## Diagram model

The diagram model is the semantic intermediate representation. `viewIntent` states whether the artifact answers an architecture, workflow, sequence, data-flow, or lifecycle question. Stable IDs connect source evidence, assets, generated cells, QA findings, and future edits. Coordinates are optional overrides; semantics must not depend on them.

Node kinds are open but should follow the route notation. Edge kinds should describe meaning (`sync`, `async`, `publish`, `retrieval`, `write`, `response`, `deny`) rather than appearance (`blue-arrow`).

## Generated Draw.io

The builder writes uncompressed `mxGraphModel` XML so other agents and version control can inspect it. Every generated node/edge carries `nc-*` metadata, and the root carries view intent, route, archetype, and model hash. A page-sized tagged background produces deterministic exports. Synced SVG marks are embedded as data URIs.

## State transitions

Asset lifecycle:

```text
Requested → Resolved → Synced → Embedded → RenderVerified
                    ↘ NeedsManual
```

Native generic glyphs may remain `Resolved`; file-backed marks must reach `RenderVerified` for a complete project.

Project readiness:

```text
pending → plan → build → diagram QA → render → awaiting visual review → postflight → complete
```

`project_state.json` records each stage's canonical input, dependency, and output
hashes. Any source/model/visual artifact change marks the affected stage stale
and invalidates downstream stages. A failed stage is retryable without deleting
the project, while a matching passing stage is reused. `complete` is valid only
when visual approval and postflight both match the current files. See
[deterministic pipeline state](../docs/pipeline-state.md).
