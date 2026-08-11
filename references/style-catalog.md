# Workflow Visual Style Catalog

Choose information depth first, then visual style. Treat these as two independent coordinates:

| Diagram type | Color Visual | Compact Monochrome |
|---|---:|---:|
| Architecture Overview | Supported | Supported |
| Detailed Request Flow | Supported | Supported |

Never treat a catalog entry as a fixed layout. Derive boundaries, tracks, cards, branches, and badges from the source content after the user chooses the two coordinates.

## Color Visual

Preview: `../assets/examples/architecture-overview.png`

Use when the diagram benefits from fast scanning, visible technology identity, presentation impact, or a mixed technical and non-technical audience.

- Use a restrained bright palette to distinguish request, processing, data, response, optional service, and error semantics.
- Prefer verified service logos and selected neutral task glyphs.
- Use pale boundary fills, clear headers, and compact technical cards.
- Keep color semantic. Do not recolor every card merely for decoration.
- Preserve the shared connector, density, badge, and source-accuracy rules.

## Compact Monochrome

Preview: `../assets/examples/compact-monochrome-system-flow.png`

Use when the user wants an academic, implementation-documentation, black-and-white, compact, relationship-led, or print-friendly diagram.

- Read and apply [compact-monochrome-style.md](compact-monochrome-style.md).
- Use black, charcoal, white, and restrained gray; allow one subtle accent only when it has structural meaning.
- Prefer compact labeled cards, nested boundaries, cylinders for persistent stores, and concise relationship labels.
- Use identical local lifecycle badges inside an agent or capability boundary when the order is real.
- Remove labels that merely repeat endpoint names, and place necessary labels in reserved pockets away from connector shafts.

## Reference-led

Use when the user supplies a visual reference or explicitly requests another style.

- Show the bundled catalog only if it helps compare options; do not override an explicit reference choice.
- Extract palette, density, shape hierarchy, icon treatment, connector language, and whitespace.
- Reproduce the grammar natively in Draw.io without copying the reference topology or claiming its original authoring tool.

## Intake contract

When type or style is unresolved, present the choice in this order:

1. **Diagram type:** Architecture Overview, Detailed Request Flow, or both.
2. **Visual style:** Color Visual, Compact Monochrome, or a supplied reference.
3. **Language and use:** language plus audience/destination in one compact question.

Display the two type previews first, then the two style previews. The style preview demonstrates visual grammar only; its subject and component count are not reusable defaults. Record the selected pair in the diagram brief, for example:

```text
Diagram profile: Architecture Overview × Compact Monochrome
```
