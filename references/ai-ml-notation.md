# AI and ML architecture notation

AI diagrams must distinguish probabilistic model behavior from deterministic application logic, source evidence from generated output, and offline lifecycle from online execution.

## AI solution overview

Show the product/user journey first, then AI-specific responsibilities: prompt/context construction, model/provider boundary, tools/retrieval, guardrails, storage, and telemetry. State where sensitive data crosses provider or trust boundaries. Do not label the entire application “AI.”

## ML lifecycle and MLOps

Separate these concerns when present:

- data collection, labeling, validation, and feature generation;
- experiment/training compute and tracking;
- evaluation gates and human approval;
- model/feature/artifact registry;
- deployment/serving and rollout strategy;
- prediction/feature drift, quality, latency, cost, and safety monitoring;
- feedback, retraining triggers, rollback, and retirement.

Distinguish CI (code), CT (training), and CD (deployment). Show versioned artifacts and promotion boundaries. Avoid a circular lifecycle graphic unless the feedback mechanism is real and labeled.

## RAG

Use two explicit lanes or boundaries.

Offline indexing:

```text
sources → extract/normalize → chunk/enrich → embed → vector/index store
```

Online serving:

```text
user query → query transform/embed → retrieve → filter/rerank → context/prompt → model → grounded answer/citations
```

Show the cross-lane read from retrieval to the index. Identify metadata/ACL filtering, citations, cache, guardrails, or fallback only when supported. Do not draw “vector DB → LLM” as if the database autonomously calls the model.

## Agentic RAG and orchestration

An agent is a control loop with state, decisions, tool calls, observations, and termination—not merely an LLM box. Show:

- user/task ingress;
- orchestrator/router/planner responsibility;
- agent roles and handoff/delegation direction;
- tool/API/data boundaries and least authority;
- short-term/session/durable state distinctions;
- retrieval and generation path;
- guardrails/policy enforcement;
- failure, retry budget, human escalation, and stop conditions;
- final evidence-bearing response.

Avoid anthropomorphic peer-agent clouds with unlabeled arrows. Every handoff should state what moves (task, context, artifact, approval) and who retains authority.

## Inference trace

Use a sequence layout for one request. Include preprocessing, policy checks, retrieval/tool calls, model inference, postprocessing/validation, response, and telemetry. Show parallel calls and streaming only if they are real. Label timeouts/retries/fallbacks; do not collapse them into a generic “AI service.”

## Evaluation and observability

Separate offline evaluation datasets/runs from online production traces. Identify evaluator type:

- deterministic metric or rule;
- model-based judge;
- human review;
- production/business outcome.

Show aggregation, thresholds, alert/action ownership, slice analysis, drift, latency, tokens/cost, safety, groundedness, and task success only as required. A model judge is probabilistic evidence, not ground truth.

## AI governance

Connect use case, dataset, model/provider, deployment, owner, risk tier, control, approval evidence, monitoring, incidents, and retirement. Distinguish policy decision from technical enforcement. Show where documentation/model cards/evaluation reports become approval evidence.
