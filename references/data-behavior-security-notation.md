# Data, behavior, delivery, product, and security notation

## Sequence and request traces

Participants run left to right; time runs top to bottom. Number or order messages in the model. Separate request, response, callback, retry, and failure. Label protocol/payload where it helps implementation. A datastore is a participant only when a concrete interaction touches it.

For request traces, start at the real ingress and finish at the observed response/outcome. Show authority decisions before protected actions. Do not infer a queue, cache, retry, or transaction boundary without evidence.

## BPMN and state

BPMN uses explicit start/end events, tasks, gateways, and pools/lanes. Sequence flow stays inside a pool; message flow crosses pools. Gateways state the decision; outgoing edges state conditions.

State machines show stable states, not operations. Transitions use trigger `[guard] / action` when those details are known. Mark initial/final states and impossible/error states only when they matter.

## ERD and data flow

ERD entities need relevant fields with PK/FK markers and typed cardinality/optionality. Do not use arrows that imply data movement for relationships.

ETL/ELT and lineage are directional. Separate storage assets from jobs/transforms. Show orchestration, quality gates, schema/contract checks, checkpoints, and sensitive-data boundaries when evidenced. Streaming views must use explicit asynchronous semantics and name topics/events.

## CI/CD and operations

Delivery flows distinguish source change, build/test, immutable artifact, policy approval, environment deployment, release strategy, verification, and rollback. DevSecOps controls belong at the stage where they execute; do not create a decorative “security” lane with no enforcement effect.

Observability distinguishes signal production, collection, storage/query, analysis/alert, and human/automated response. Show logs, metrics, and traces unless deliberately scoped out. Incident response uses ownership lanes and explicit communication/review loops.

## Security

Trust boundaries are visual contracts. Name the trust basis and show every relevant crossing. Zero-trust views should identify subject/workload identity, policy decision point, policy enforcement point, resource, and telemetry/continuous evaluation.

Auth flows must distinguish authorization code, access token, ID token, session, and credential where relevant. Arrow direction follows actual transmission. Never print secret values.

Threat models connect assets, entry points, trust crossings, threats, and mitigations. Make residual/unmitigated risk visible. Classification views state handling rules for storage, transfer, access, retention, and disposal.

## Product and service views

User flows represent user actions and system states, not backend microservices. Sitemaps represent information hierarchy. Wireframes prioritize layout and affordance over brand polish. Service blueprints align customer evidence/actions with frontstage, backstage, and support processes across explicit lines of interaction/visibility.
