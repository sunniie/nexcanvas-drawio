# Enterprise reference-architecture visual grammar

Use this reference for cloud, data, AI/ML, integration, deployment, and platform diagrams that should resemble the official technical documentation of a large cloud provider. This is a structural grammar, not a decorative theme.

## Select the archetype before layout

Set `presentation.visualArchetype` in diagram model V3:

- `microsoft-reference`: Microsoft Architecture Center-style phase columns, neutral connectors, green numbered steps, and a platform band.
- `aws-reference`: the same reference composition with AWS-neutral line and badge colors; use only official AWS icons.
- `google-cloud-reference`: the same reference composition with Google Cloud-neutral line and badge colors; use only official Google Cloud icons.
- `provider-neutral-reference`: phase-based technical documentation without vendor branding.
- `technical-editorial`: the card-based visual system for conceptual, product, and mixed-vendor views where icon-led reference architecture is not appropriate.

Do not use a provider archetype merely because the diagram mentions one provider. Use it when the requested artifact is a concrete component, data-flow, deployment, or reference-architecture view whose nodes form a visual bill of materials.

## Composition contract

1. Use a white page and choose a composition from [reference-image-patterns.md](reference-image-patterns.md). Three to seven pale phase columns are the default for ordered lifecycles, not a universal template.
2. Put the phase name at the top center. Use spatial order as the primary hierarchy instead of colored card borders.
3. Represent concrete provider services with unmodified official icons, normally 48-64 px, and place the official product name immediately below the icon.
4. Reserve card shapes for custom applications, logical functions, or explicit nested groups. Do not put every provider service inside a rounded card.
5. Use thin, dark, single-direction, orthogonal connectors. Avoid bidirectional arrows; split request and response when both matter.
6. Label only relationships that are not self-evident. Use transparent offset labels in clear gutters, opaque callouts for deliberate text breaks on long rails, and standalone notes beside elbows. Read [connector-label-routing.md](connector-label-routing.md).
7. Add consistent numbered badges to the main narrative path. A badge belongs to a flow, not to a service.
8. Use thin solid groups for deployment or ownership scope and dashed groups for optional, runtime, or logical scope. Explain any non-obvious line or border semantics in a compact legend.
9. Put identity, secrets, observability, governance, security, and cost controls in a horizontal foundation band when they apply across phases.
10. Keep open whitespace around service icons. Density comes from purposeful grouping and flow, not oversized containers.
11. Avoid arbitrary line intersections. Give parallel flows independent lanes; converge only through a node or a documented semantic bus.

Run [layout-brainstorming.md](layout-brainstorming.md) before drawing. Sparse pipelines use outlined equal stages; dense lifecycles use weighted stages and reserved rails; feedback systems may use a hybrid grid; high-centrality systems may use a hub; network and deployment views use nested topology frames.

## Model fields

Reference diagrams use these presentation fields:

```json
{
  "semantics": {
    "groups": [
      {"id": "ingest", "label": "Ingest", "kind": "phase", "provenance": []},
      {"id": "platform", "label": "Platform", "kind": "foundation", "provenance": []}
    ],
    "entities": [
      {"id": "source", "label": "Telemetry", "kind": "source", "provenance": []},
      {"id": "events", "label": "Azure Event Hubs", "caption": "Streaming ingestion", "kind": "service", "provenance": []}
    ],
    "relationships": [
      {"id": "flow-1", "source": "source", "target": "events", "kind": "data", "label": "Stream events", "provenance": []}
    ]
  },
  "presentation": {
    "visualArchetype": "microsoft-reference",
    "showTitle": false,
    "groups": [
      {"semanticId": "ingest", "presentation": "phase-column", "order": 1},
      {"semanticId": "platform", "presentation": "foundation-band", "order": 9}
    ],
    "entities": [
      {"semanticId": "source", "boundary": "ingest"},
      {"semanticId": "events", "presentation": "service-icon", "assetRef": "azure-event-hubs", "boundary": "ingest"}
    ],
    "relationships": [
      {"semanticId": "flow-1", "lineClass": "control", "step": 1}
    ]
  }
}
```

Use `lineClass: data` only when a distinct provider accent is materially useful. Use `optional` or `dependency` for dashed paths. Prefer neutral black/dark connectors for the primary narrative.

## Official guidance incorporated

The implementation follows these provider-owned sources:

- Microsoft Azure Architecture Center: https://learn.microsoft.com/en-us/azure/architecture/
- Microsoft diagramming practices and official-icon rules: https://learn.microsoft.com/en-us/azure/well-architected/architect-role/design-diagrams
- Microsoft Azure icon package and terms: https://learn.microsoft.com/en-us/azure/architecture/icons/
- AWS Architecture Icons: https://aws.amazon.com/architecture/icons/
- Google Cloud official icon library: https://cloud.google.com/icons

Treat provider pages as authoritative for naming, icon versions, and usage terms. Recheck them when refreshing a provider pack.
