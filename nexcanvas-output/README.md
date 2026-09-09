# Generated diagram projects

This is NexCanvas Draw.io's default output root when `nexcanvas init`
is run without an explicit project directory.

```text
nexcanvas-output/
└── <project-slug>/
    ├── source_model.json
    ├── diagram_lock.json
    ├── diagram_model.json
    ├── project_state.json
    ├── assets/
    ├── artifacts/
    │   ├── diagram.drawio
    │   └── diagram.drawio.png
    └── reports/
```

Generated projects under this folder are ignored by this repository. The
reference projects that ship with the skill live under [`examples/`](../examples/).

When the skill is installed inside another repository, the default path is
relative to that repository's current working directory, not the installed
skill directory. Pass an explicit project directory when a different location
is required.
