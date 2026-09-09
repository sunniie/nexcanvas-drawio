# ADR 0001: Use a canonical semantic model

- Status: accepted
- Date: 2026-09-09

## Decision

NexCanvas treats semantic entities and relationships as the canonical diagram
meaning. Source evidence and presentation geometry are separate layers. The
Draw.io XML is a generated, editable delivery artifact rather than the only source
of truth.

## Consequences

Repository synchronization can compare meanings without treating coordinate or
style changes as architectural changes. Future schema work must provide stable
semantic IDs and preserve user-owned presentation edits during reconciliation.
