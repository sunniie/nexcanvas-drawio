# ADR 0002: Keep Draw.io as the primary delivery format

- Status: accepted
- Date: 2026-09-09

## Decision

NexCanvas emits native, uncompressed, editable mxGraph XML and embeds resolved
assets. PNG, SVG, and PDF are derived preview or publishing formats.

## Consequences

Users retain editor independence and can inspect changes in version control.
NexCanvas must preserve editability and must never satisfy this contract by placing
a flattened screenshot on a Draw.io canvas.
