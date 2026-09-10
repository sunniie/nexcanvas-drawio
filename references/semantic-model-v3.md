# Semantic Model V3

Read this reference when creating, editing, validating, or migrating
`diagram_model.json` schema `3.0`.

## Layer ownership

V3 keeps one portable JSON contract while giving each kind of information one
owner:

| Layer | Owns | Must not own |
|---|---|---|
| `metadata` | title, intent, route, audience, delivery context, language, evidence-model link, assumptions | entities, coordinates, connector routes |
| `semantics` | stable group/entity/relationship IDs, labels, kinds, endpoints, behavior, fields, fact provenance | icons, emphasis, geometry, lanes, style |
| `presentation` | theme, archetype, canvas, group placement, asset choice, importance, geometry, labels, lanes, ports, step badges | architectural identity or relationship endpoints |
| `source_model.json` | sources, atomic facts, citations, repository revisions, confidence | diagram geometry |
| `artifacts/` and `reports/` | generated Draw.io, previews, build and QA evidence | canonical meaning |

Every semantic group, entity, and relationship has a globally unique stable
`id`. Presentation records use `semanticId` and must cover every semantic record
exactly once. Renaming a label does not require changing the ID. Do not derive an
ID from a coordinate, array index, theme, or current file line.

## Provenance

Every semantic record contains a `provenance` array. Each entry has exactly:

```json
{"factId": "fact-query", "confidence": "confirmed"}
```

`factId` must exist in the linked `source_model.json`. Confidence is one of
`confirmed`, `inferred`, or `unknown` and must match that fact. Use an empty array
for a deliberately illustrative record with no factual claim; do not fabricate a
source. QA rejects unknown fact IDs and confidence drift.

## Minimal shape

```json
{
  "schemaVersion": "3.0",
  "metadata": {
    "title": "Checkout request",
    "viewIntent": "sequence",
    "route": {"family": "behavior", "profile": "request-trace"},
    "audience": "backend engineers",
    "deliveryTarget": "engineering-doc",
    "language": "en",
    "evidenceModel": "source_model.json",
    "assumptions": []
  },
  "semantics": {
    "groups": [],
    "entities": [
      {"id": "client", "label": "Client", "kind": "actor", "provenance": []},
      {"id": "api", "label": "Checkout API", "kind": "service", "provenance": []}
    ],
    "relationships": [
      {"id": "request", "source": "client", "target": "api", "kind": "sync", "label": "POST /checkout", "provenance": []}
    ]
  },
  "presentation": {
    "theme": "technical-editorial",
    "visualArchetype": "technical-editorial",
    "showTitle": false,
    "direction": "LR",
    "canvas": {"width": 1600, "height": 900},
    "groups": [],
    "entities": [
      {"semanticId": "client", "importance": "primary"},
      {"semanticId": "api", "importance": "primary"}
    ],
    "relationships": [
      {"semanticId": "request", "lineClass": "control", "labelMode": "offset", "layout": {"order": 1}}
    ],
    "legend": []
  }
}
```

The full machine-readable contract is
[`schemas/diagram-model-v3.schema.json`](../schemas/diagram-model-v3.schema.json).

## Migration from V2

Write a new file; keep the original until the V3 result has passed build and QA:

```bash
nexcanvas migrate v2-to-v3 diagram_model.json \
  --source-model source_model.json \
  --output diagram_model.v3.json
```

The source model is auto-discovered beside the V2 file when its conventional
name is used. Migration preserves node, edge, and boundary IDs; moves visual
fields into presentation; preserves unclassified extension data; and returns a
machine-readable semantic fingerprint. Existing output is rejected unless
`--force` is explicit. Input and output may never be the same path.

After inspection, a project may adopt V3 by moving the new file to
`diagram_model.json`, rebuilding, rendering, visually approving, and completing
postflight. V2 remains readable throughout `v0.4.x`.

## Fingerprints and edits

Draw.io output from V3 records both `nc-model-hash` and `nc-semantic-hash`.
Changing presentation changes the full model hash but must leave the semantic
fingerprint unchanged. Changing an entity, relationship, endpoint, or provenance
changes both. Reordering semantic arrays does not change the semantic fingerprint;
ordering belongs to presentation. The `v0.4.x` pipeline conservatively rebuilds
after either kind of change; presentation-aware incremental reconciliation
belongs to a later phase.
