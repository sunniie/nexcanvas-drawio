# Layout brainstorming contract

Run layout brainstorming after the semantic model is stable and before geometry is generated. This stage prevents a renderer from forcing every architecture into the same set of columns.

## Inputs

The brainstormer reads `diagram_model.json` and measures:

- node, edge, boundary, and ordered-phase counts;
- number of nested boundaries and containment ratio;
- branch nodes, feedback/back edges, and graph cycles;
- maximum node degree and hub score;
- maximum nodes per phase and cross-boundary edge ratio;
- canvas aspect ratio and requested direction;
- declared delivery target and any explicit `layoutStrategy`.

## Candidate layouts

Score every candidate even when one is later selected explicitly:

- `compact-pipeline`: sparse, low-branching, three-to-six-stage stories;
- `phase-columns`: normal left-to-right lifecycles;
- `dense-phase-columns`: large multi-branch lifecycles with nested groups and rail lanes;
- `phase-rows`: top-to-bottom stories or portrait targets;
- `hybrid-grid`: process/store feedback, loops, or two-dimensional macro areas;
- `hub-and-spoke`: one service is the clear exchange or analytical center;
- `nested-topology`: network, region, deployment, ownership, or product containment dominates.

The report must include all scores and rationales, not only the winner. An explicit model strategy overrides the recommendation but does not suppress the comparison.

## Decision flow

1. If containment ratio is high or boundaries name topology scopes such as region, VNet, subnet, cluster, account, or deployment, evaluate `nested-topology` first.
2. If one node has a hub score of at least 0.30, evaluate `hub-and-spoke` first.
3. If feedback edges or cycles are material, prefer `hybrid-grid` over a forced lifecycle.
4. For ordered phases, select `compact-pipeline` when there are at most ten nodes and little branching; select `dense-phase-columns` when there are at least sixteen nodes, a phase contains four or more nodes, or multiple nested groups are present; otherwise select `phase-columns`.
5. Switch to `phase-rows` when the canvas is portrait/narrow or the declared direction is top to bottom.
6. Record why the selected layout beats the runner-up and which constraints remain manual.

## Geometry plan

The chosen plan defines:

- orientation and canvas recommendation;
- stage weights based on direct node and child-group demand;
- whether outline or filled phase containers are appropriate;
- whether a foundation band is useful;
- whether top/bottom rails are needed;
- a connector-lane map, label-pocket map, and any real semantic buses;
- the step-badge policy;
- a list of manual review risks such as high feedback, a weak hub, or excessive density.

Nodes may set `layout.track` from `0.0` to `1.0` to align related services across phase columns. Edges may set `layout.rail` to `top`, `bottom`, or an absolute Y coordinate for long bypass paths and `layout.lane` to separate repeated rails/gutters. Select `labelMode`, `labelPlacement`, `laneId`, and any justified `busId` using [connector-label-routing.md](connector-label-routing.md). These are deterministic layout controls, not arbitrary pixel placement.

For `hub-and-spoke`, assign each top-level boundary `layout.role` as `source`, `ingest`, `hub`, `consumer`, or `satellite`. Common aliases such as `sources`, `ingress`, `analytical-hub`, `insights`, and `advanced-analytics` are normalized automatically. Use `presentation: hub-ring` for the single central analytical service, outline groups for source/ingest/consumer towers, and `layout.flow: row` for a lower enrichment zone. If roles are omitted, the renderer falls back to semantic order, but explicit roles are preferred for reviewable architecture models.

## Command

```bash
python <skill-root>/scripts/layout_brainstorm.py <project-dir>/diagram_model.json --output <project-dir>/reports/layout_brainstorm.json
```

Review the report before building. If the selected candidate is wrong, set `layoutStrategy` explicitly and document the reason in `diagram_lock.json`.
