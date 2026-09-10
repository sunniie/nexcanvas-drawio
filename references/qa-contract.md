# Quality contract

Quality is a sequence of independent gates. Passing one gate never implies that later gates pass.

## Gate 1: contract validity

Validate schema version, required fields, IDs, cross-references, routes, themes, canvas, and asset states. Errors block generation.

## Gate 2: semantic/profile validity

Intent rules first check that the artifact answers one dominant question: structure, work progression, ordered communication, data movement, or state transition. The specialized profile then adds notation-specific rules. Examples:

- RAG needs offline indexing, online retrieval, and generation.
- ERD needs fields and relationship cardinality.
- BPMN needs start/end events and ownership lanes.
- zero trust needs trust boundaries and identity/policy enforcement.
- MLOps needs training, deployment/serving, and monitoring feedback.
- sequences/traces need participants, messages, ordering, and useful protocol labels.

V3 provenance IDs on semantic groups/entities/relationships must resolve to
source facts, and each recorded confidence must match its fact. Presentation
records must cover every stable semantic ID exactly once and cannot redefine it.

For repository sources, QA must receive `--repo-root` and verify origin, full commit, cited blob when supplied, repo-relative path, and line range. Missing or mismatched repository evidence blocks release; verification proves source provenance, not live runtime behavior.

## Gate 3: asset validity

Requested marks must resolve in `asset_manifest.json`. File-backed SVG must exist locally and pass safety validation. Reject remote image URLs, unresolved exact marks, and misleading substitutes.

## Gate 4: structural and geometry QA

The combined QA runs canonical model/build metadata checks plus the established
`drawio_qa.py` heuristics. Fix:

- overlaps and connector-through-node crossings;
- wrong terminal entry/exit directions;
- missing edge geometry;
- duplicate cells or model/build drift;
- unlabeled relationships whose meaning is required;
- insufficient label clearance;
- connector-through-label, label/label, and label/badge collisions;
- unrelated connectors that cross or share a lane without a semantic `busId`;
- independent edges that attach to the same node coordinate and create an ambiguous fan-in, fan-out, or visual relay;
- callouts that do not mask their own line or conceal an unrelated line;
- rendered title or legend cells that disagree with `showTitle` or the model legend;
- excessive support/chrome area, sparse cards, and unbalanced composition;
- real services represented as plain unlabeled boxes when a verified mark is required.

Use `--fail-on-warning` for release artifacts. Warnings may be accepted only after documented visual review.

## Gate 5: render integrity

The Draw.io CLI export must exist, be non-empty, preserve editable diagram data, and report dimensions/hash. A successful subprocess exit alone is insufficient.

## Gate 6: visual review

View the actual PNG/SVG at original resolution and target display size. Check clipping, line/text collisions, hierarchy, balance, direction, marks, and legibility. For every icon-led node, verify that the icon, title, and caption occupy distinct vertical bands with visible clearance; a title or caption touching the icon is a release blocker. Trace every primary connector end to end, then inspect connector terminals, fan-in/fan-out port separation, callout breaks, lane separation, and badge exclusion zones again at 200%. Record concrete notes. `nexcanvas generate --approve-visual` is an attestation, not an automated aesthetic score.

When no image-view capability exists, leave `pending-review`. Do not self-approve from XML.

## Gate 7: postflight provenance

Postflight requires confirmed source/lock, matching hashes, passing QA, approved visual artifact, no unresolved assets, and unchanged outputs. It emits artifact hashes for delivery.

Completion means postflight `ok: true`, not merely “the file opens.”

The supported automation path is `nexcanvas generate`. Its state machine must
remain `awaiting-review` while Gate 6 is pending and may set project status to
`complete` only after Gate 7 passes against the current hashes. See
[deterministic pipeline state](../docs/pipeline-state.md).
