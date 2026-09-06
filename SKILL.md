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
- Repair, restyle, or extend an existing `.drawio`: [workflows/repair.md](workflows/repair.md)
- Recreate a screenshot, slide, Mermaid/PlantUML result, or visual reference: [workflows/convert-reference.md](workflows/convert-reference.md)

Always read:

- [references/intake-and-discovery.md](references/intake-and-discovery.md)
- [references/project-contract.md](references/project-contract.md)
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

1. Run `python <skill-root>/scripts/doctor.py` and record whether Draw.io Desktop rendering is available.
2. Infer one dominant `viewIntent`: architecture, workflow, sequence, data-flow, or lifecycle. Do not ask the user to choose when the brief is clear.
3. Investigate only the source evidence required by that intent. For repository-backed facts, pin Git origin/revision and exact file/line ranges; separate confirmed facts, assumptions, and exclusions in `source_model.json`.
4. Select one of the 48 profiles in `config/route-registry.json` as the specialized notation beneath the intent.
5. Build `diagram_model.json`, then run layout brainstorming. Compare alternatives before locking orientation and composition.
6. Confirm intent, audience, delivery target, route, notation, layout strategy, theme, canvas, source hash, and asset policy in `diagram_lock.json`.
7. Resolve exact official logos from verified catalogs or provider-owned packs. Use neutral native glyphs for internal concepts. Never substitute a neighboring product logo.
8. Build native, uncompressed mxGraph XML. Do not paste a screenshot onto a Draw.io canvas.
9. Run contract, intent, profile, repository-evidence, geometry, connector, asset, render, and visual QA.
10. Inspect the rendered image at target size and connector terminals at enlarged scale. Iterate from the model/layout input, then run postflight.

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

## Portable commands

Initialize at the standard output location:

```bash
python <skill-root>/scripts/project.py init --name "<title>" --brief "<user brief>" --language <language>
```

An explicit project directory remains supported:

```bash
python <skill-root>/scripts/project.py init <project-dir> --name "<title>" --brief "<user brief>" --language <language>
```

Build and gate after completing the contracts:

```bash
python <skill-root>/scripts/layout_brainstorm.py <project-dir>/diagram_model.json --output <project-dir>/reports/layout_brainstorm.json
python <skill-root>/scripts/build_drawio.py <project-dir>/diagram_model.json -o <project-dir>/artifacts/diagram.drawio --project-root <project-dir> --proof <project-dir>/reports/build.json
python <skill-root>/scripts/diagram_qa.py <project-dir>/diagram_model.json --drawio <project-dir>/artifacts/diagram.drawio --source-model <project-dir>/source_model.json --project-root <project-dir> --output <project-dir>/reports/diagram_qa.json --fail-on-warning
python <skill-root>/scripts/render.py <project-dir>/artifacts/diagram.drawio -o <project-dir>/artifacts/diagram.drawio.png --report <project-dir>/reports/render.json
```

Only after actually viewing the preview:

```bash
python <skill-root>/scripts/visual_qa.py <project-dir>/artifacts/diagram.drawio.png --expected-width <width> --expected-height <height> --approve --reviewer "<reviewer>" --notes "<specific observations>" --output <project-dir>/reports/visual_qa.json
python <skill-root>/scripts/postflight.py <project-dir> --output <project-dir>/reports/postflight.json
```

If Draw.io Desktop is unavailable, produce and structurally validate the editable
`.drawio`, leave visual approval pending, and state the limitation explicitly.

## Delivery contract

For a completed project, deliver the editable `.drawio`, rendered preview,
source/model/lock contracts, asset manifest, and QA reports. State the selected
route, evidence snapshot, assumptions, output directory, and whether postflight
passed. Do not claim completion while actionable warnings or unreviewed renders
remain.
