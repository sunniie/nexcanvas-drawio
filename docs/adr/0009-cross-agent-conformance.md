# ADR 0009: Evidence-based cross-agent conformance

- Status: accepted
- Date: 2026-09-10

## Context

NexCanvas is installed through different discovery paths in Codex, GitHub
Copilot, Claude Code, and other Agent Skills hosts. The hosts may interpret the
same natural-language instructions differently, expose different tools, or stop
at different workflow stages. Prompt similarity and a visually plausible image
therefore do not demonstrate equivalent behavior.

Duplicating the complete workflow for every host would create several sources of
truth. Those copies would drift independently and make a passing host adapter
meaningless when the shared skill changes.

## Decision

NexCanvas uses one shared skill and deterministic CLI core. A host adapter is a
small data contract that records only discovery paths, runtime detection,
invocation guidance, evidence requirements, and known limitations. It must not
duplicate the drawing workflow.

Cross-agent conformance is measured against versioned corpus cases and observable
project artifacts. Each result reports five independent dimensions:

1. semantic coverage;
2. evidence and provenance;
3. asset resolution;
4. route and layout planning;
5. delivery-gate completion.

The conformance scorer is deterministic. It evaluates a completed project and
does not award credit for prose claims in an agent transcript. Fixture results
exercise the scorer but can never establish host support.

A host may be reported as `verified` only when an observed run includes the host
identity, adapter version, skill digest, corpus-case digest, timestamps, execution
evidence, and the evaluated project artifact digests. Other explicit states are
`not-run`, `unavailable`, and `failed`.

## Consequences

- Host behavior can be compared without requiring byte-identical diagrams.
- Semantic and delivery regressions are visible by dimension.
- CI can validate the corpus, adapters, schemas, scorer, and fixtures without
  pretending to execute proprietary hosts.
- Real host verification remains an external integration test and must be
  refreshed when the skill, adapter, or corpus digest changes.
- A published capability matrix can contain unavailable or not-run hosts; those
  entries are limitations, not passing evidence.

