# NexCanvas Draw.io

**A source-aware Draw.io skill for Codex that turns real system behavior into polished, editable technical diagrams.**

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Draw.io](https://img.shields.io/badge/Draw.io-editable-f97316.svg)](https://www.drawio.com/)
[![Codex Skill](https://img.shields.io/badge/Codex-skill-2563eb.svg)](https://developers.openai.com/codex/skills/)

NexCanvas Draw.io is designed for architecture diagrams, detailed request flows, network diagrams, ERDs, sequence diagrams, and other technical visuals. It adds a collaborative discovery workflow, content-driven layouts, semantic icon planning, connector geometry rules, and automated QA on top of native Draw.io XML generation.

The repository contains one standalone Codex skill. Future NexCanvas repositories can use the same family naming, for example `nexcanvas-slides` or `nexcanvas-docs`, while remaining independently installable.

## Example output

The examples below are real Draw.io exports with editable source files. Click an image to view it at full resolution.

### Architecture Overview

[![Learning website architecture overview](assets/examples/architecture-overview.png?v=20260811-vimic)](assets/examples/architecture-overview.png)

[Open the editable `.drawio` source](examples/learning-website-architecture-overview.drawio)

### Detailed Request Flow

[![Python practice detailed request flow](assets/examples/detailed-request-flow.png?v=20260811-vimic)](assets/examples/detailed-request-flow.png)

[Open the editable `.drawio` source](examples/learning-website-python-practice-detailed-request.drawio)

## What makes this skill different

- **Collaborative intake:** it asks for diagram mode, language, audience, scope, and source material when those choices are not already known.
- **Content-driven composition:** sections, tracks, component counts, and step numbers are derived from the actual system rather than copied from a fixed template.
- **Two workflow modes:** Architecture Overview for system boundaries and responsibilities; Detailed Request Flow for concrete interactions, state changes, responses, and failures.
- **Source-aware modeling:** the skill inspects repositories, documentation, screenshots, and attachments before proposing the diagram structure.
- **Useful iconography:** verified product logos are used for real services, while Draw.io-native semantic glyphs illustrate internal tasks such as validation, OCR, scoring, queues, and persistence.
- **Strict connector rules:** arrows attach to component perimeters, use short orthogonal routes, enter on the intended side, and avoid text or unrelated cards.
- **Visual QA:** bundled checks cover overlaps, crossings, attachment geometry, density, support-zone dominance, response detours, badge consistency, and workflow-specific composition.
- **Editable deliverables:** repository documentation can keep both the native `.drawio` file and an embedded-XML `.drawio.png` preview.

## Requirements

| Requirement | Purpose | Required? |
|---|---|---|
| [Codex](https://developers.openai.com/codex/) | Runs the skill | Yes |
| Git | Installs or updates the repository | Yes |
| Python 3.10+ | Runs the bundled QA script and tests | Recommended |
| [Draw.io Desktop](https://github.com/jgraph/drawio-desktop/releases/latest) | Opens diagrams, provides offline shape libraries, and exports embedded previews | Strongly recommended |

The skill can still create native `.drawio` files without Draw.io Desktop. Desktop is recommended because it makes local editing, logo-library access, and deterministic PNG/SVG/PDF export much easier.

## Install the Codex skill

### Recommended: use `$skill-installer`

Open Codex and send:

```text
$skill-installer Install the Draw.io skill from https://github.com/sunniie/nexcanvas-drawio and name it drawio.
```

Let the installer choose the configured Codex skill directory. Restart Codex only if the newly installed skill does not appear in the next session.

### Manual global installation

Current Codex installations discover personal skills under `~/.agents/skills`. The commands below refuse to overwrite an existing `drawio` skill.

#### Windows PowerShell

```powershell
$skillTarget = Join-Path $HOME ".agents\skills\drawio"
if (Test-Path -LiteralPath $skillTarget) {
    throw "A skill already exists at $skillTarget"
}
New-Item -ItemType Directory -Force -Path (Split-Path $skillTarget) | Out-Null
git clone https://github.com/sunniie/nexcanvas-drawio $skillTarget
```

#### macOS or Linux

```bash
skill_target="$HOME/.agents/skills/drawio"
test ! -e "$skill_target" || { echo "A skill already exists at $skill_target"; exit 1; }
mkdir -p "$(dirname "$skill_target")"
git clone https://github.com/sunniie/nexcanvas-drawio "$skill_target"
```

Some Codex installations and installer configurations use `$CODEX_HOME/skills` (commonly `~/.codex/skills`). If that is your configured skill directory, clone the repository to `$CODEX_HOME/skills/drawio` instead.

### Repository-scoped installation

To share the skill only with collaborators in one codebase, place it at:

```text
YOUR_PROJECT/.agents/skills/drawio
```

Commit that folder or add this repository as a Git submodule according to your team's dependency policy.

### Verify discovery

Start a fresh Codex session and try:

```text
Use $drawio to create an Architecture Overview for this repository. Inspect the source first and show me the proposed diagram brief before drawing.
```

Codex should identify the `drawio` skill and begin its intake or source-discovery flow.

## Install Draw.io Desktop

Download the newest stable release from the official [Draw.io Desktop releases page](https://github.com/jgraph/drawio-desktop/releases/latest). Avoid pinning installation instructions to a particular version because the desktop application is updated regularly.

### Windows

Choose the package that fits your environment:

- **Installer `.exe`:** normal machine installation; commonly places the CLI at `C:\Program Files\draw.io\draw.io.exe`.
- **MSI:** useful for managed or per-user deployment where administrator rights may be restricted.
- **Portable `.exe`:** no installation or file association; useful on locked-down machines.

The per-user executable may be located at:

```text
C:\Users\YOUR_NAME\AppData\Local\Programs\draw.io\draw.io.exe
```

### macOS

Install the universal package and verify the CLI at:

```text
/Applications/draw.io.app/Contents/MacOS/draw.io
```

### Linux

Use the release package appropriate for your distribution (`.deb`, `.rpm`, or AppImage). When installed on `PATH`, verify it with:

```bash
drawio --version
```

## Enable logo and shape libraries

Draw.io Desktop includes built-in shape libraries that work offline. To make diagrams richer and more accurate:

1. Open Draw.io Desktop.
2. Select **More Shapes...** at the bottom of the left shape panel.
3. Enable only the libraries relevant to your work, such as **General**, **Flowchart**, **UML**, **Network**, **AWS**, **Azure**, **Google Cloud**, **Kubernetes**, or **Cisco**.
4. Use the shape search with both product names and semantic synonyms—for example `document`, `OCR`, `validation`, `queue`, `gateway`, or `database`.
5. Keep official service logos for the service they actually represent. Use neutral Draw.io glyphs for internal tasks or concepts that do not have an official brand mark.

Useful official resources:

- [Search for shapes in Draw.io](https://www.drawio.com/docs/manual/shapes/shape-search/)
- [Work with the shape panel](https://www.drawio.com/docs/manual/editor/panels/shapes-panel/)
- [Public custom libraries](https://www.drawio.com/docs/manual/shapes/public-custom-libraries/)
- [Draw.io icon libraries](https://icons.diagrams.net/)
- [Official `drawio-libs` repository](https://github.com/jgraph/drawio-libs)

### Import an extra local library

Draw.io Desktop does not provide the web editor's extended external clip-art search while offline. For extra icons:

1. Download a trusted Draw.io library file, normally `.xml` or `.drawio`, from an official or reviewed source.
2. In Draw.io Desktop, choose **File → Open Library From → Device**.
3. Select the downloaded library and keep it in the left shape panel for the current workspace.

Do not substitute a nearby vendor logo when the exact product icon is unavailable. A clearly labeled generic symbol is more accurate than an invented brand association.

## How to use the skill well

You can simply ask for a diagram, but the best results come from supplying the audience, source, and desired output. The skill reuses known context and should not ask you to repeat information already available.

### Architecture Overview

Use this mode for a README, slide, portfolio, system map, ownership boundary, or high-level dependency view.

```text
Use $drawio to create an English Architecture Overview for new backend engineers.
Inspect this repository as the source of truth. Show system boundaries, primary
responsibilities, real dependencies, and verified service logos. Keep the main
workflow dominant and deliver both .drawio and .drawio.png.
```

### Detailed Request Flow

Use this mode for an endpoint, user interaction, state transition, debugging path, or implementation-level behavior.

```text
Use $drawio to create a Detailed Request Flow for the profile scan interaction.
Separate independent HTTP requests into tracks, show request/response/error lanes,
include status codes and fallbacks verified from source, and deliver editable source
plus an embedded PNG preview.
```

### Let the skill help define scope

```text
Use $drawio for this system. I am not sure whether I need an Architecture Overview
or Detailed Request Flow. Show the bundled examples, ask for the missing language,
audience, and scope, then propose a concise diagram brief before drawing.
```

### Other diagram types

```text
Use $drawio to create an ERD from the database migrations in this repository.
Mark inferred relationships as assumptions, use English labels, and export an
editable PNG with the native .drawio source.
```

## Recommended workflow

1. **Discover:** inspect the supplied code, documents, screenshots, and known conversation context.
2. **Classify:** choose Architecture Overview, Detailed Request Flow, or another appropriate diagram type.
3. **Confirm:** propose real boundaries, tracks, events, dependencies, icon plan, language, and output format.
4. **Model:** build native Draw.io XML from the confirmed content model.
5. **Validate:** run XML and visual heuristics with the matching QA profile.
6. **Export:** create `.drawio.png`, SVG, or PDF with embedded diagram XML when needed.
7. **Inspect:** review at 100% for hierarchy and at 200% for connector attachment and arrow direction.

The number of zones, tracks, cards, and sequence badges must follow the subject. The examples are visual references, not fixed templates.

## Output formats

| Output | Best use | Editable in Draw.io? |
|---|---|---|
| `.drawio` | Canonical source | Yes |
| `.drawio.png` | README preview and editable image artifact | Yes, when exported with embedded XML |
| `.drawio.svg` | Scalable documentation asset | Yes, when exported with embedded XML |
| `.drawio.pdf` | Review or print | Yes, when exported with embedded XML |
| Browser URL | Quick collaborative editing | Yes, subject to browser URL-size limits |

For repository documentation, keep both the native source and the embedded PNG preview.

## Export from the command line

After locating the Draw.io executable, export with embedded XML:

```bash
drawio -x -f png -e -b 10 -o architecture.drawio.png architecture.drawio
```

Windows PowerShell example:

```powershell
& "C:\Program Files\draw.io\draw.io.exe" `
  -x -f png -e -b 10 `
  -o architecture.drawio.png architecture.drawio
```

The important flag is `-e` / `--embed-diagram`. It keeps the exported PNG, SVG, or PDF editable when reopened in Draw.io.

## Run quality checks

From the repository root:

```bash
python scripts/drawio_qa.py examples/learning-website-architecture-overview.drawio --diagram-type overview
python scripts/drawio_qa.py examples/learning-website-python-practice-detailed-request.drawio --diagram-type detailed
python -m unittest discover -s scripts -p "test_*.py"
```

Before publishing a diagram, resolve every `ERROR` and all actionable `WARNING` results, then inspect the rendered image. Automated XML checks cannot determine whether the composition is attractive or whether every edge communicates the intended business meaning.

## Repository structure

```text
.
├── SKILL.md                         # Codex skill entry point
├── agents/openai.yaml              # UI metadata
├── references/
│   ├── intake-and-discovery.md      # Collaborative intake workflow
│   ├── visual-contract.md           # Shared visual and geometry rules
│   └── workflow-types.md            # Overview vs. Detailed Request guidance
├── scripts/
│   ├── drawio_qa.py                 # Diagram QA CLI
│   └── test_drawio_qa.py            # Standard-library unit tests
├── assets/examples/                 # README-ready PNG examples
└── examples/                        # Editable Draw.io example sources
```

## Troubleshooting

### The skill is not discovered

- Confirm `SKILL.md` is directly inside the installed `drawio` folder.
- Start a new Codex session after installation.
- Check whether your installation uses `~/.agents/skills` or a configured `$CODEX_HOME/skills` directory.
- Invoke it explicitly as `$drawio` in the first prompt.

### Draw.io export is unavailable

- Confirm Draw.io Desktop is installed.
- Locate the platform-specific executable listed above.
- If export is still unavailable, keep the native `.drawio` file or ask for browser URL output.

### Logos are missing

- Enable the relevant libraries through **More Shapes...**.
- Search by vendor, product, and generic semantic terms.
- Import a reviewed local library when the built-in set is insufficient.
- Prefer a labeled generic glyph over an incorrect vendor logo.

### The diagram is technically valid but still looks weak

- Compare the export beside the selected visual reference at the same scale.
- Reduce low-information cards and redistribute real components across unused space.
- Add semantic task glyphs where text-only stages become visually repetitive.
- Shorten response routes and ensure the primary path remains visually dominant.
- Recheck contrast, label gutters, logo scale, and repeated badge consistency.

## Contributing

Issues and pull requests are welcome. When changing the QA script or visual rules:

1. Add or update a standard-library unit test.
2. Run the complete test suite.
3. Validate both editable examples with their matching diagram profiles.
4. Export and visually inspect both previews before submitting the change.

## License

Released under the [MIT License](LICENSE).
