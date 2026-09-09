# Semantic intents and repository evidence

NexCanvas separates the question a diagram answers from the visual grammar used to draw it. Every new diagram resolves one dominant `viewIntent`; the route then selects the specialized notation and QA profile. Microsoft/reference styling, canvas orientation, and Draw.io output remain independent presentation decisions.

## Five semantic intents

| Intent | Primary question | Nodes emphasize | Edges mean |
|---|---|---|---|
| `architecture` | What exists, where is it, and what depends on what? | Components, services, stores, actors, boundaries | Dependency or communication |
| `workflow` | What work happens from start to outcome? | Tasks, decisions, roles, approvals, exceptions | Execution order and branching |
| `sequence` | Who communicates with whom, and in what order? | Participants or lifelines | Calls, messages, callbacks, and returns |
| `data-flow` | Where does data originate, transform, persist, and get consumed? | Sources, transforms, stores, consumers | Data movement, payload, or lineage |
| `lifecycle` | Which states can one entity enter, and what triggers transitions? | Initial, active, waiting, failure, and terminal states | Events, guards, or transition conditions |

Choose the intent from the user's question, not from a preferred visual template. One repository may justify several diagrams, but one artifact should keep one dominant question. Do not ask the user to choose from this list when the brief already makes the intent clear. Use `nexcanvas intent` only as a deterministic hint; the agent remains responsible for resolving material ambiguity.

Profiles refine an intent. For example, `architecture` may use C4, deployment, cloud-reference, RAG, or agent-orchestration. Some profiles are deliberately compatible with more than one intent: RAG can be an architecture or data-flow view; agent orchestration can be architecture, workflow, or sequence. The model and lock record the chosen intent explicitly.

## Intent-specific repository reading

Read only the evidence required by the selected view:

- `architecture`: entry points, deploy/runtime configuration, component boundaries, external dependencies, stores, ownership, and trust boundaries;
- `workflow`: triggers, ordered handlers/jobs, decisions, retries, approvals, failure paths, and terminal outcomes;
- `sequence`: concrete caller/callee chain, transport, sync/async behavior, returns, timeouts, and callbacks for one bounded scenario;
- `data-flow`: producers, payloads, schemas, transformations, queues/topics, stores, retention/sensitivity, and consumers;
- `lifecycle`: state definitions, transition events, guards, retry/cancellation behavior, persistence, and terminal states.

Do not inventory an entire repository. Start from a bounded question, trace the primary path, then include only side paths necessary to explain it.

## Revision-pinned repository contract

Repository-backed facts use a repository source pinned to its origin and full commit:

```json
{
  "id": "repo-1",
  "type": "repository",
  "location": "../..",
  "snapshot": "<full-commit>",
  "repository": {
    "remote": "https://github.com/example/project.git",
    "revision": "<full-commit>",
    "dirty": false,
    "capturedAt": "2026-09-06T00:00:00Z"
  }
}
```

Facts may cite exact repository ranges:

```json
{
  "id": "fact-checkout-entry",
  "claim": "POST /checkout enters the checkout service handler.",
  "confidence": "confirmed",
  "evidence": [
    {
      "sourceId": "repo-1",
      "path": "src/checkout/routes.ts",
      "startLine": 24,
      "endLine": 41,
      "blob": "<git-blob-hash>",
      "label": "checkout route"
    }
  ]
}
```

Capture repository identity without authoring claims:

```bash
nexcanvas analyze capture <repo-root> --source-model <project-dir>/source_model.json --source-id repo-1
```

After adding fact ranges, verify origin, revision, blob, path, and lines:

```bash
nexcanvas analyze verify <project-dir>/source_model.json --repo-root <repo-root> --output <project-dir>/reports/repository_evidence.json
```

Repository verification proves that cited bytes and ranges exist at the pinned revision. It does not prove a runtime deployment, business owner, or inferred behavior. Keep such claims as assumptions unless separately evidenced. A repository source without an explicit local `--repo-root` fails release QA; uncommitted work is never silently treated as part of the pinned commit.

## Delivery invariants

- `diagram_model.viewIntent` and `diagram_lock.viewIntent` must agree.
- The route must be compatible with the intent.
- Every diagram node/edge evidence ID must resolve to a source fact.
- Repository-backed release QA and postflight must receive the same explicit repository root and reverify the pinned evidence.
- Draw.io embeds `nc-view-intent`, route, archetype, and model hash as inspectable metadata.
- Semantic intent never selects a visual style. Apply the established user reference and NexCanvas visual grammar only after the content model is stable.
