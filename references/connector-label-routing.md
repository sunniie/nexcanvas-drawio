# Connector and label routing

Use this reference for workflow, cloud, data, AI/ML, network, deployment, and other diagrams where connectors carry substantial meaning. It captures the line and annotation grammar used in official provider reference architectures.

## Plan before routing

Create a connector ledger before geometry:

1. Classify each edge as primary flow, data, dependency, response, feedback, error, or semantic bus.
2. Remove labels that merely repeat the source, target, or obvious direction.
3. Reserve horizontal or vertical gutters between phases, groups, and node rows.
4. Assign independent `laneId` values to parallel flows. Reuse a segment only when the edges belong to the same real bus and share a `busId`.
5. Assign a distinct source and target perimeter port to every independent fan-in, fan-out, or relay edge. Reserve separate left/right/top/bottom ports before routing the surrounding lanes.
6. Place long bypass paths on explicit top or bottom rails. Give separate rails separate `layout.lane` values or absolute coordinates.
7. Choose the label mode and reserve its rectangle before placing badges.

Do not treat line jumps as the default cure for a crowded route. Repack nodes, widen a gutter, select another orientation, add a rail, or use a semantic hub first.

## Label modes

Every edge label uses one mode:

| Mode | Use | Rendering rule |
|---|---|---|
| `none` | The relationship is obvious from endpoints and direction | Keep semantic text in the model if useful, but do not render it |
| `offset` | Short payload, action, condition, or protocol | Transparent standalone text beside the longest clear segment |
| `callout` | Long text placed on a long rail or deliberate trunk | Opaque standalone text centered on its own line, intentionally masking only that line |
| `note` | Secondary explanation near an elbow or connector gutter | Transparent, muted/italic text outside the stroke |

`callout` is not permission to hide poor routing. It is valid only when the label intersects its own edge and no unrelated edge passes beneath its rectangle. `offset` and `note` labels must not touch any connector.

Use `labelPlacement` to choose a stable pocket:

```json
{
  "labelMode": "callout",
  "labelPlacement": {
    "segment": 2,
    "t": 0.55,
    "side": "center",
    "width": 172,
    "height": 26
  }
}
```

- `segment` indexes the routed polyline segment.
- `t` selects a point from `0.0` to `1.0` along that segment.
- `side` is `auto`, `above`, `below`, `left`, `right`, or `center`.
- `offset` controls the text-edge gap for non-centered labels.
- `dx` and `dy` provide small final adjustments.
- `width` and `height` override the estimated label rectangle when wrapping is required.

Prefer semantic placement over pixel nudging. Use `labelPlacement.dx/dy` only for a final adjustment after choosing a clear segment and side.

## Lanes, rails, and buses

- `laneId` documents the independent corridor used by an edge. Parallel request/response or data/control flows need different lane IDs.
- `layout.rail` accepts `top`, `bottom`, or an absolute Y coordinate.
- `layout.lane` separates multiple named top, bottom, left, or right routes; the default spacing is 36 px and can be changed with `layout.laneSpacing`.
- `layout.midX` and `layout.midY` move the single elbow corridor for an ordinary orthogonal route.
- `layout.sourcePort` and `layout.targetPort` accept normalized perimeter coordinates such as `[1.0, 0.35]` or `[0.5, 1.0]`. Use them to separate multiple relationships at a service; do not attach an incoming edge and an unrelated outgoing edge to the same point.
- `layout.waypoints` supplies reviewed absolute `[x, y]` bends only when rails, gutters, and midpoint controls cannot express a dense route. Keep the route orthogonal and document why the detour is meaningful.
- `busId` permits shared connector geometry only when the shared segment represents one real publish, fan-out, merge, or backbone relationship.
- `allowCrossing` is an exceptional documented escape hatch for a reviewed unavoidable crossing. Do not use it to make release QA pass without visual evidence.

## Collision contract

Apply this matrix at release QA:

```text
edge x node             -> error
edge x unrelated label  -> error
edge x own callout       -> allowed
edge x own offset/note   -> error
label x label            -> error
label x step badge       -> error
edge x unrelated edge    -> error
independent edges share a node port -> error
same semantic bus        -> allowed when busId matches
```

An incoming edge and outgoing edge that meet at the same service port form an ambiguous visual relay even when the XML contains two edge objects. The release gate rejects this pattern. Move one relationship to another perimeter side or coordinate. The only exception is a real, labeled semantic bus with a shared `busId`.

Step badges are intentional line interrupters. Keep them identical and reserve their rectangle after label placement; a badge may cover its associated line but never a label.

## Visual review

At 100%, trace every primary route from its visible source port to its visible target port and confirm the label belongs to exactly one line. At 200%, inspect callout edges, badge intersections, elbow terminals, fan-in/fan-out port separation, parallel lanes, arrowhead entry, and any explicit crossing exception. A passing XML or model contract does not replace this inspection.
