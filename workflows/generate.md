# Generate a new diagram

Use this workflow for a diagram created from a prompt, repository, documentation, screenshots, or several evidence sources.

## 1. Discover the runtime and delivery target

Run `scripts/doctor.py`. Record whether rendering is available. Follow [../references/intake-and-discovery.md](../references/intake-and-discovery.md): resolve the brief and language, then infer design and delivery choices. Ask only about missing language or material content ambiguity. Carry forward any visual reference or named design standard established earlier in the conversation and select its matching archetype before building the model.

Choose canvas by target:

- README/engineering doc: 1600×900 or 1600×1000.
- Slide: 1600×900, with 12–18 primary nodes maximum.
- Poster/print: increase both dimensions but preserve readable target-size type.
- Interactive editing: size to content; still render one review preview.

Default generated work to `./nexcanvas-output/<project-slug>/` in the user's current repository. Use another path only when the user requests it or an existing project contract already establishes one.

## 2. Resolve semantic intent

Read [semantic intents and repository evidence](../references/semantic-intents-and-repository-evidence.md). Infer exactly one dominant `viewIntent` from the brief: architecture, workflow, sequence, data-flow, or lifecycle. Do not ask the user to select a type when the question is already clear. Use `scripts/view_intent.py` only as a routing hint when useful; resolve material ambiguity from evidence or one focused question.

The intent controls what the agent investigates and which semantic QA runs. It does not select a theme, provider, orientation, or visual archetype.

## 3. Build `source_model.json`

Inspect the actual sources according to the selected intent. Do not inventory every file. For repository-backed work, capture the Git identity first, then cite exact file/line ranges for confirmed facts:

```bash
python <skill-root>/scripts/repo_evidence.py capture <repo-root> --source-model <project-dir>/source_model.json --source-id repo-1
python <skill-root>/scripts/repo_evidence.py verify <project-dir>/source_model.json --repo-root <repo-root> --output <project-dir>/reports/repository_evidence.json
```

Record:

- `sources`: stable location and snapshot/commit/date;
- `facts`: atomic claims with evidence pointers and confidence;
- `assumptions`: unverified but necessary modeling decisions;
- `exclusions`: deliberately omitted scope.

Set status to `confirmed` when the source boundary and facts are ready for delivery. A draft may be built for exploration but cannot pass postflight.

## 4. Select a route

Use [../references/route-catalog.md](../references/route-catalog.md). Select the route by the question the diagram must answer, not by superficial appearance.

Examples:

- “What exists and who uses it?” → `software/c4-context`.
- “Where does each workload run?” → `runtime-cloud/deployment`.
- “What happens to one request?” → `behavior/request-trace`.
- “How does retrieval ground generation?” → `ai-ml/rag`.
- “How do agents delegate and use tools?” → `ai-ml/agent-orchestration`.
- “Where are identity and policy enforced?” → `security/zero-trust`.

## 5. Confirm `diagram_lock.json`

Before locking, select a visual archetype. Use `microsoft-reference`, `aws-reference`, or `google-cloud-reference` when the requested output is a provider-specific component/reference architecture. Use `provider-neutral-reference` for the same phase-and-foundation grammar without provider branding. Read [../references/enterprise-reference-style.md](../references/enterprise-reference-style.md).

Before choosing geometry, read [../references/reference-image-patterns.md](../references/reference-image-patterns.md) and run the brainstorm contract in [../references/layout-brainstorming.md](../references/layout-brainstorming.md):

```bash
python <skill-root>/scripts/layout_brainstorm.py <project-dir>/diagram_model.json --output <project-dir>/reports/layout_brainstorm.json
```

Compare the winner with the runner-up. Confirm whether the story is sparse or dense, whether containment or a central hub dominates, whether feedback requires a hybrid grid, and whether landscape or portrait shortens the primary paths. Set `layoutStrategy` explicitly after this review.

Lock the selected intent, route, notation, layout adapter, `layoutStrategy`, visual archetype, theme, audience, delivery target, canvas, and asset policy. Set `sourceHash` to the canonical JSON hash used by `scripts/nexcanvas/common.py::sha256_json`. Update the hash whenever the source model changes.

## 6. Write `diagram_model.json`

Model the content before drawing:

- each node has one responsibility and a notation-appropriate `kind`;
- boundaries communicate ownership, runtime, trust, lifecycle, or lane semantics—not decoration;
- every edge has direction and `kind`; add protocol, payload, authority, async, trust crossing, and evidence when meaningful;
- classify each rendered relationship label with `labelMode`; reserve `labelPlacement`, `laneId`, rails, and any real `busId` before build;
- evidence IDs must resolve to `source_model.json` facts;
- use concise labels; move explanation into `description` only when it helps the reader;
- set `layout.order` to encode a real sequence, rank, or lane order;
- set `importance=primary` for the end-to-end story so composition QA can measure it.

## 7. Resolve assets

Follow [../references/asset-policy.md](../references/asset-policy.md). Search and sync every requested exact mark before building. For internal concepts, use a generic native glyph and label. Avoid logos when shape/color would be clearer.

Provider reference diagrams must resolve service nodes from the provider-owned icon pack and must not silently fall back to Simple Icons.

## 8. Build and run QA

Build native `.drawio` with `scripts/build_drawio.py`, then run `scripts/diagram_qa.py --fail-on-warning`. For repository-backed sources, pass `--repo-root <repo-root>`; omission is a blocking error. Fix the model or layout logic rather than hiding findings with exemption tags. Exemptions are allowed only when the visual was reviewed and the heuristic is provably wrong.

## 9. Render and inspect

Render with `scripts/render.py`. Inspect at full resolution and at the actual delivery size. Check:

- title and labels are readable;
- no clipping or accidental overlap;
- primary story is immediately visible;
- boundaries have a clear reason;
- arrowheads and labels agree with direction;
- every fan-in, fan-out, and relay relationship has a visibly distinct perimeter port unless the edges intentionally share a documented semantic bus;
- bidirectional meaning is represented by separate one-way edges when necessary;
- labels do not sit on connector strokes, icons, nodes, step badges, or visible boundary outlines;
- every icon-led node keeps the icon, title, and caption in separate vertical bands; no text touches or enters the rendered icon box;
- callout labels break only their own long rail, unrelated connectors do not cross/share lanes, and labels remain clear of step badges;
- logos are visible, exact, and not distorted;
- title, subtitle, and legend chrome appears only when enabled by the model;
- dense areas and empty areas feel intentional.

Iterate until clean. Then record visual approval with `visual_qa.py` and run `postflight.py`.

## 10. Deliver

Deliver the editable `.drawio`, preview, and reports. State the semantic intent, route, evidence snapshot, assumptions, and whether repository, runtime, and visual QA completed. Repository-backed postflight must also receive `--repo-root <repo-root>`. Never describe portable-tier output as visually verified.
