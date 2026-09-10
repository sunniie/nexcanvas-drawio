# Cross-agent conformance

NexCanvas separates portable instructions from measurable execution. Codex,
GitHub Copilot, Claude Code, and other Agent Skills hosts all consume the same
root `SKILL.md`; host descriptors under `conformance/hosts/` contain discovery
and evidence metadata only.

## What is measured

Each corpus result exposes five unweighted dimensions. All must score `1.0` for
the run to pass:

| Dimension | Observable checks |
|---|---|
| Semantics | minimum graph coverage, required concepts, and required relationships |
| Evidence | confirmed source contract, grounded facts, and fact references on primary semantics |
| Assets | valid manifest, resolved embedded/render-verified references, and required exact assets |
| Routing | valid model and lock, correct semantic intent/profile, lock alignment, and layout brainstorm |
| Gates | editable Draw.io, render, diagram QA, explicit visual approval, and live postflight |

The pass threshold is intentionally conjunctive. An attractive render cannot
hide missing evidence, and a semantically correct model cannot hide an unfinished
visual gate.

## Corpus design

`conformance/suite.json` covers architecture, workflow, sequence, data flow, and
lifecycle. Cases specify semantic invariants rather than coordinates or exact XML,
so hosts may make legitimate presentation choices while remaining comparable.
The dense architecture and multi-agent workflow cases point to tracked reference
projects used as evaluator fixtures. These fixtures verify the scorer, not a host.

## Result trust model

There are four matrix states:

- `verified`: an observed passing run with hash-bound execution evidence;
- `failed`: an observed run failed at least one required dimension;
- `not-run`: the adapter is defined but no current observed result exists;
- `unavailable`: the host executable is not visible in the inspected environment.

An observed record binds the host/case identity, timestamps, invocation surface,
request, skill, adapter, corpus case, and evidence files by SHA-256. Result
digests additionally bind the evaluated project artifacts. A change to any
versioned input makes an older result historical rather than current proof.

## Why output is not byte-identical

The agent owns interpretation, evidence investigation, and rendered-image review.
The deterministic core owns contracts, compilation, structural QA, hashes, and
gate order. Different hosts may choose different valid wording or geometry, so
conformance evaluates the communicated meaning and delivery guarantees instead
of requiring identical Draw.io XML.

## Current published status

The repository ships adapters and a deterministic conformance harness. No host is
declared verified by fixture data. See the generated
[published host capability matrix](host-capability-matrix.md) and the
[execution workflow](../workflows/conformance.md).
