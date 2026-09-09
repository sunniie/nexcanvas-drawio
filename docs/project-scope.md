# Project scope

## Mission

NexCanvas is a portable AI-agent skill and architecture compiler that transforms
technical briefs, repositories, and visual references into polished, editable,
evidence-grounded Draw.io diagrams.

Its differentiator is the complete artifact lifecycle: semantic intent, source
evidence, content-driven layout, verified assets, native Draw.io generation,
rendered review, and machine-readable quality proof.

## Supported work

NexCanvas supports creating, repairing, and converting technical diagrams for
software, cloud, data, security, delivery, product, and AI/ML systems. It can
represent architecture, workflow, sequence, data-flow, and lifecycle views.

Repository-backed claims must cite verifiable source locations and revisions.
Brief-only claims must be explicitly identified as user-supplied or assumed.

## Non-goals

NexCanvas is not:

- a replacement for the Draw.io editor, Microsoft Visio, or collaborative canvas;
- a BPMN/DMN execution engine or business-process runtime;
- a promise to infer deployed infrastructure or runtime behavior from source alone;
- a prompt collection whose correctness depends only on one agent following prose;
- a reason to substitute an approximate vendor logo for an unverified exact asset;
- a hosted service or telemetry platform in the current technical-preview phase.

## Responsibility boundary

Agents handle architectural judgment: resolving a brief, identifying material
ambiguity, interpreting evidence, proposing semantics, and reviewing a render.

Deterministic tooling handles contracts, state transitions, asset provenance,
layout mechanics, Draw.io compilation, structural checks, hashes, and postflight.
An agent must not declare completion when a required deterministic gate is absent
or failed.

## Source-of-truth order

For repository-backed work, truth is ordered as follows:

1. pinned and verified source evidence;
2. explicit user statements and decisions;
3. recorded, reviewable assumptions;
4. generated semantic and presentation artifacts.

The Draw.io file is an editable deliverable, not the sole semantic source of truth.
Future synchronization must reconcile repository changes with user edits rather
than blindly regenerating the canvas.

## Completion definition

A diagram project is complete only when required contracts validate, exact assets
are local and embedded, structural QA passes, the current artifact is rendered,
the render is visually inspected, and postflight verifies all relevant hashes.
