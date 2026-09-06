# Repair or extend an existing Draw.io diagram

Use this workflow when the user supplies `.drawio` or asks to correct, modernize, restyle, or extend an existing diagram.

## Preserve before changing

Work on the supplied file or a clearly named copy according to the request. Do not flatten the diagram into an image. Preserve pages, editable cell labels, IDs when external references may depend on them, and any user assets not proven obsolete.

Run the legacy geometry audit first:

```bash
python <skill-root>/scripts/drawio_qa.py <input.drawio> --qa-profile <baseline|composition|interaction>
```

Inspect the rendered current state when Draw.io Desktop is available. Structural findings and visual findings are separate evidence.

## Reconstruct semantics

Create a v2 project beside the repaired artifact. Extract or infer:

- nodes and their responsibilities;
- boundaries and their actual semantics;
- edge direction, relationship type, labels, protocols, and payloads;
- technology marks and whether they are exact;
- the source basis for changed factual claims.

Put these into `source_model.json`, `diagram_lock.json`, and `diagram_model.json`. For a purely visual repair, source facts may point to the original diagram while assumptions explicitly state that system behavior was not revalidated.

## Repair priorities

Apply in this order:

1. factual and directional correctness;
2. wrong/missing product identities;
3. notation violations and ambiguous boundaries;
4. connector crossings, bad terminal sides, and label collisions;
5. hierarchy, density, whitespace, typography, color, and polish.

If the existing topology is fundamentally unsuitable, rebuild from the semantic model and retain the original as a reference. Do not preserve poor geometry merely to minimize the diff.

## Verify

Run the complete v2 build/QA/render/visual/postflight cycle. Compare before and after at the same scale. Report what was repaired, what was intentionally preserved, and which behavioral claims were or were not revalidated.
