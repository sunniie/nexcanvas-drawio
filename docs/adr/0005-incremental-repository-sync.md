# ADR 0005: Reconcile repository changes incrementally

- Status: accepted
- Date: 2026-09-09

## Decision

Future repository synchronization will use a three-way comparison between the
previous semantic snapshot, newly analyzed repository facts, and current user
edits. It will update only affected semantic and presentation regions.

## Consequences

Low-confidence removals must be reported rather than silently deleted. Manual
labels, annotations, positions, and unaffected connector routes are preserved.
Full regeneration remains an explicit user choice, not the default sync behavior.
