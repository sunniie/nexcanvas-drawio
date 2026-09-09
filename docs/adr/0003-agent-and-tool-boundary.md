# ADR 0003: Separate agent judgment from deterministic enforcement

- Status: accepted
- Date: 2026-09-09

## Decision

Agents interpret briefs, investigate evidence, resolve ambiguity, propose semantic
models, and visually review renders. Deterministic commands enforce schemas, stage
order, assets, layout mechanics, compilation, structural QA, and provenance.

## Consequences

Instructions remain portable, but correctness does not depend on a particular
agent remembering every workflow step. Cross-agent claims require conformance
tests against observable artifacts and invariants.
