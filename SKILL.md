---
name: nexcanvas-drawio
description: Create, repair, convert, render, and verify editable Draw.io diagrams for software, cloud, data, security, delivery, product, and AI/ML architecture. Use for architecture maps, workflows, flowcharts, ERDs, sequences, BPMN, network views, wireframes, .drawio files, or PNG/SVG/PDF diagram exports.
license: MIT
---

# NexCanvas Draw.io

Create evidence-grounded technical diagrams that remain editable, portable, and
visually reviewable. Use the contract-first pipeline in this skill instead of
drawing unsupported boxes directly from a thin prompt.

## Select the workflow

Read exactly one primary workflow:

- New diagram from a request, repository, document, or mixed evidence: [workflows/generate.md](workflows/generate.md)
- Update an existing repository-backed V3 project after source changes: [workflows/sync-repository.md](workflows/sync-repository.md)
- Repair, restyle, or extend an existing `.drawio`: [workflows/repair.md](workflows/repair.md)
- Recreate a screenshot, slide, Mermaid/PlantUML result, or visual reference: [workflows/convert-reference.md](workflows/convert-reference.md)

When measuring whether this skill behaves consistently in another agent host,
read [workflows/conformance.md](workflows/conformance.md). Conformance is an
evaluation workflow, not a substitute for one of the drawing workflows above.

Always read:

- [references/intake-and-discovery.md](references/intake-and-discovery.md)
- [references/project-contract.md](references/project-contract.md)
- [references/semantic-model-v3.md](references/semantic-model-v3.md)
- [references/asset-policy.md](references/asset-policy.md)
- [references/qa-contract.md](references/qa-contract.md)

Load only the references needed for the selected route:

- Semantic intent and repository-backed work: [references/semantic-intents-and-repository-evidence.md](references/semantic-intents-and-repository-evidence.md)
- Route selection: [references/route-catalog.md](references/route-catalog.md)
- Software, runtime, and cloud: [references/software-cloud-notation.md](references/software-cloud-notation.md)
- Data, behavior, security, delivery, and product: [references/data-behavior-security-notation.md](references/data-behavior-security-notation.md)
- AI/ML, RAG, agents, evaluation, and governance: [references/ai-ml-notation.md](references/ai-ml-notation.md)
- Visual system and connector rules: [references/visual-system-v2.md](references/visual-system-v2.md) and [references/connector-label-routing.md](references/connector-label-routing.md)
- Microsoft/AWS/Google reference architecture: [references/enterprise-reference-style.md](references/enterprise-reference-style.md), [references/reference-image-patterns.md](references/reference-image-patterns.md), and [references/provider-icon-packs.md](references/provider-icon-packs.md)
- Layout selection: [references/layout-brainstorming.md](references/layout-brainstorming.md)

## Intake contract

Use [brief-first intake](references/intake-and-discovery.md): resolve the brief and
diagram language, then proceed. Select route, detail, style, orientation and canvas
internally from the content. Do not offer preset type/style menus or ask how many
diagram types the user wants. Ask only for missing language or a material content
ambiguity. A concise brief is a decision record, not a routine approval gate.
Visual references and named standards already established in the conversation remain
authoritative across later examples and revisions; brief-first intake does not reset
them to the default theme.

## Standard project location

Unless the user chooses another path, write generated work to:

```text
<current-working-directory>/nexcanvas-output/<project-slug>/
```

This is the user's repository or working directory, never the installed skill
directory. The output project contains semantic contracts, local assets, the
editable artifact, previews, and QA reports.

## Required pipeline

1. Run `nexcanvas doctor` and record whether Draw.io Desktop rendering is available.
2. Infer one dominant `viewIntent`: architecture, workflow, sequence, data-flow, or lifecycle. Do not ask the user to choose when the brief is clear.
3. Investigate only the source evidence required by that intent. For repository-backed facts, pin Git origin/revision and exact file/line ranges; separate confirmed facts, assumptions, and exclusions in `source_model.json`.
4. Select one of the 48 profiles in `config/route-registry.json` as the specialized notation beneath the intent.
5. Build `diagram_model.json` schema `3.0`: keep stable groups, entities, relationships, and fact provenance in `semantics`; keep icons, emphasis, geometry, label placement, connector lanes, and routes in `presentation`. Compare plausible layout alternatives before locking orientation and composition; the orchestrator persists the scored brainstorm report.
6. Confirm intent, audience, delivery target, route, notation, layout strategy, theme, canvas, source hash, and asset policy in `diagram_lock.json`.
7. Resolve exact official logos from verified catalogs or provider-owned packs. Use neutral native glyphs for internal concepts. Never substitute a neighboring product logo.
8. Run `nexcanvas generate <project-dir>` to plan, build native uncompressed mxGraph XML, run strict diagram QA, and render. Do not paste a screenshot onto a Draw.io canvas.
9. Treat exit code `3` as an external visual-review gate. Inspect the rendered image at target size and connector terminals at enlarged scale; never approve from XML or command output alone.
10. Iterate from model/layout inputs. When the current render is actually approved, rerun `generate` with `--approve-visual`, reviewer, and specific notes. Completion requires the orchestrated postflight stage.

## Visual rules that cannot be waived silently

- Derive landscape, portrait, columns, rows, hub-and-spoke, or hybrid composition from content density and flow direction.
- Use boundaries only for ownership, runtime, trust, lifecycle, phase, or lane meaning.
- Route primary connectors orthogonally and attach them to shape perimeters.
- Give every independent fan-in, fan-out, and relay relationship a distinct perimeter port. A service must never look like an unlabeled continuation point between unrelated edges.
- Separate request/response, publish/consume, success/failure, and data/control when meanings differ.
- Render a relationship label only when it adds an action, payload, state, or result not obvious from the endpoints.
- Keep every label clear of nodes, icons, step badges, unrelated connector strokes, and every visible container or hub outline. Clear interior space is allowed; cutting through a border is not.
- Preserve independent icon and text bands inside icon-led nodes. Never allow a node kind, description, or manual layout override to shrink the title or caption into the icon box.
- Use opaque callouts only to break their own long rail. Never use a white label box to hide an unrelated crossing.
- Give independent flows separate lanes. Share a `busId` only when the diagram represents a real semantic bus.
- Embed synced SVG data so logos survive cloning and offline use.
- Never call XML-only output visually verified.

## Unified CLI

Prefer the installed `nexcanvas` command. If the host has cloned the skill but
has not installed the Python package, use
`python <skill-root>/scripts/nexcanvas_cli.py` as the command prefix. Both invoke
the same CLI and resolve bundled configuration and assets independently of the
current working directory. Do not call the deprecated one-file script entry
points in new workflows.

Initialize at the standard output location:

```bash
nexcanvas init --name "<title>" --brief "<user brief>" --language <language>
```

An explicit project directory remains supported:

```bash
nexcanvas init <project-dir> --name "<title>" --brief "<user brief>" --language <language>
```

Build, gate, and safely resume after completing the contracts:

```bash
nexcanvas generate <project-dir>
```

Only after actually viewing the preview:

```bash
nexcanvas generate <project-dir> --approve-visual --reviewer "<reviewer>" --notes "<specific observations>"
```

For repository-backed evidence, pass `--repo-root <repo-root>` on every
`generate` invocation. Read `project_state.json` or the JSON command result to
distinguish reused, rerun, failed, and awaiting-review stages. Do not bypass the
orchestrator with stale reports when claiming completion.

For a V2 project, keep the original model and create a separate V3 candidate:

```bash
nexcanvas migrate v2-to-v3 <project-dir>/diagram_model.json --output <project-dir>/diagram_model.v3.json
```

Inspect and validate the candidate before adopting it as `diagram_model.json`.
Never put coordinates, styles, icons, label placement, or connector routes back
into V3 semantic records.

For a repository-backed V3 project whose source has evolved, read
[workflows/sync-repository.md](workflows/sync-repository.md) and preview the
three-way reconciliation before applying it:

```bash
nexcanvas sync <project-dir> --repo-root <repo-root> --dry-run
nexcanvas sync <project-dir> --repo-root <repo-root> --apply
```

Never confirm a removal without tracing its stable ID to the repository change.
Sync preserves current presentation records and reports same-field conflicts
instead of overwriting user edits.

If Draw.io Desktop is unavailable, produce and structurally validate the editable
`.drawio`, leave visual approval pending, and state the limitation explicitly.

## Delivery contract

For a completed project, deliver the editable `.drawio`, rendered preview,
source/model/lock contracts, asset manifest, and QA reports. State the selected
route, evidence snapshot, assumptions, output directory, and whether postflight
passed. Do not claim completion while actionable warnings or unreviewed renders
remain.
