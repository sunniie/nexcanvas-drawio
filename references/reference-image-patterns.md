# Reference-image layout patterns

Use this reference when a user supplies one or more official architecture diagrams as a visual target. Analyze the references as layout systems before copying colors or icons. The numbered patterns below correspond to the seven Microsoft examples used to calibrate NexCanvas v2.

## 1. Wide data and machine-learning lifecycle

- Five macro zones run left to right: sources, ingest, train/deploy, consume, plus a full-width platform band.
- Column widths are unequal. The train/deploy zone is deliberately wider because it contains two nested execution modes and more relationship text.
- The primary story moves horizontally, while long top and bottom rails carry streaming and batch bypass paths.
- Green step badges sit on handoffs. A repeated number denotes parallel alternatives, not duplicate services.
- Notes occupy connector gutters; they do not compete with product labels.

Choose `dense-phase-columns` for this composition. Reserve top and bottom rail lanes before placing nodes.

## 2. Compact medallion analytics architecture

- Ingest is a narrow left column, process is the upper middle, store is the lower middle, and serve occupies the upper/right area.
- Process-to-store feedback is more important than a strict phase sequence.
- A governance strip spans the bottom, visually separated from the workload.
- Short vertical links and a few numbered handoffs make the loop legible.

Choose `hybrid-grid` when feedback between processing and storage would make phase columns produce long return edges.

## 3. Dense Synapse analytics architecture

- Sources and consumers form stable left and right towers.
- One large central ownership boundary spans ingest, store, process, and enrichment capabilities.
- Nested rectangles communicate product and workload scope more strongly than background columns.
- One highlighted blue path is shown against quieter gray context paths.
- Governance and platform capabilities use separate horizontal support bands.

Choose `nested-topology` when containment and ownership answer the reader's question better than lifecycle stages. Use line hierarchy instead of numbering every edge.

## 4. IoT analytics hub architecture

- A source tower occupies the left; streaming ingestion sits left-center; a central analytical store is the visual anchor.
- Consumers form a tall right-side output column; advanced analytics sits below the hub.
- Connections form an L-shaped and radial system around the analytical store.
- Numbered badges identify important ingestion, query, and ML exchanges.

Choose `hub-and-spoke` when one service has materially higher degree and narrative importance than all peers. Place sources left, consumers right, and secondary enrichment below the hub.

## 5. Network and deployment topology

- One large region or virtual-network frame contains nested subnet frames.
- External actors sit outside the frame; CI/CD actors may sit above it; managed resources sit below or inside their owning subnet.
- Connections describe reachability and deployment, not lifecycle progression.
- Numbered markers annotate setup or deployment operations without turning every peer relation into a step.

Choose `nested-topology` when network, region, subscription, cluster, or ownership boundaries dominate.

## 6. Compressed model lifecycle

- Six stages fit into one wide horizontal narrative.
- A large processing frame contains an internal sub-pipeline and several substeps.
- A risk-management rail spans the stages that it governs.
- Step labels use hierarchical suffixes such as `3a`, `3b`, and `3c` for work inside one macro step.

Choose `phase-columns` when one linear story dominates, even if one stage needs a much larger width. Use nested groups for substeps rather than creating more top-level columns.

## 7. Sparse document-processing pipeline

- Five equal outlined columns contain only one to three services each.
- Phase labels sit above the content and the page keeps generous whitespace.
- Only four cross-stage handoffs are numbered.
- No foundation band is shown because cross-cutting services are not part of the question.

Choose `compact-pipeline` for ten or fewer nodes, low branching, and three to six ordered phases. Use outline phases, equal or nearly equal widths, and omit support bands unless they are material.

## Rules derived across all references

### Orientation

- Prefer landscape when the dominant semantic order is left to right, there are three or more stages, or consumers and sources must anchor opposite sides.
- Prefer portrait or `phase-rows` when the delivery target is narrow, the story is primarily top to bottom, or vertical stacking shortens most edges.
- Do not rotate a topology merely to fill the canvas. Orientation follows reading order and containment.

### Density

- Sparse diagrams use outline phases, equal stage widths, fewer labels, and more whitespace.
- Dense diagrams use weighted stage widths, nested groups, reserved connector gutters, and explicit top/bottom rail lanes.
- Density is justified by relationships and grouping, not by enlarging background containers.

### Steps and callouts

- Put badges on active handoffs, never on passive stores or services.
- Use repeated numbers or suffixes for parallel branches of the same macro step.
- Omit numbering when containment and line hierarchy already communicate the story.
- Put explanatory text in connector gutters or dedicated notes; keep service labels short.

### Edge hierarchy

- Primary flow: dark solid line or provider accent when the reference requires it.
- Context/dependency: thinner neutral or dashed line.
- Optional/async: dashed line with a short label.
- Long bypass flow: top or bottom rail, kept outside node rows.

### Line and label collision treatment

- Prevent crossings through layout first: align peers, reserve gutters, and give parallel flows independent lanes.
- Omit labels when phase order and endpoints already explain the handoff.
- Put short labels above or below a clear straight segment.
- On long top/bottom rails, use a compact opaque callout that intentionally hides only its own line.
- Treat green step badges as intentional line interrupters, but keep label rectangles out of the badge exclusion zone.
- Permit shared trunks only for a real merge, fan-out, or backbone; document them with a shared `busId`.
