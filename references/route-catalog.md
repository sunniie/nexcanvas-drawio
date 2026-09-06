# Route catalog

Routes are specialized notations beneath one dominant semantic intent. Resolve
`architecture`, `workflow`, `sequence`, `data-flow`, or `lifecycle` first using
[semantic intents and repository evidence](semantic-intents-and-repository-evidence.md),
then choose the profile that best answers the bounded question. Do not expose the
catalog as a mandatory questionnaire.

Select a profile by the architectural question. The route registry is authoritative for notation, layout adapter, and base geometry QA profile.

## Enterprise

| Profile | Question answered | Required semantics |
|---|---|---|
| `capability-map` | What can the organization do? | Capability hierarchy, domain grouping, maturity/priority only when evidenced |
| `value-stream` | How is value created end to end? | Ordered stages, entry/exit value, accountable capabilities |
| `enterprise-landscape` | How do business, application, data, and technology concerns align? | Explicit layers/viewpoints and dependency direction |
| `stakeholder-map` | Who influences or is affected by the system? | Central subject, stakeholder classes, influence/interest meaning |

## Software

| Profile | Question answered | Required semantics |
|---|---|---|
| `c4-context` | Who uses the system and what external systems interact with it? | People, focal system, external systems, labeled relationships |
| `c4-container` | What deployable/runnable parts make up the system? | Containers, responsibilities, technologies, boundaries, relationships |
| `c4-component` | What components collaborate inside one container? | Component responsibility, technology where useful, containing context |
| `dependency` | What depends on what? | Direction, dependency type, cycles/hotspots if relevant |
| `uml-class` | What are the static types and relationships? | Attributes/operations as needed, multiplicity, inheritance/association semantics |

## Runtime and cloud

| Profile | Question answered | Required semantics |
|---|---|---|
| `deployment` | Where does each software unit run? | Runtime nodes, deployed artifacts, environment/region boundaries |
| `cloud-reference` | How are cloud services composed? | Exact services, accounts/subscriptions/projects, zones/regions, network/data flow |
| `network-topology` | How can traffic traverse the network? | Zones, subnets, endpoints, protocols/ports where supported, direction |
| `kubernetes` | How are workloads and platform resources arranged? | Cluster/namespace, workload, service/ingress, config/secret/storage boundaries |
| `integration` | How do systems exchange messages/data? | Source/target, protocol, sync/async, broker/API, ownership, payload |

## Behavior

| Profile | Question answered | Required semantics |
|---|---|---|
| `sequence` | In what order do participants exchange messages? | Participants, ordered messages, sync/async, returns/alternatives when relevant |
| `request-trace` | What happens to one concrete request? | Entry, protocol, authoritative checks, persistence/events, response/failure |
| `event-choreography` | How do services react to events without a central controller? | Producers, event names, consumers, async direction, idempotency/failure notes |
| `bpmn` | How is business work coordinated? | Start/end events, tasks, gateways, pools/lanes, sequence/message flows |
| `state-machine` | How can an entity change state? | Initial/final states, transition trigger/guard/action |
| `algorithm-flow` | How does an algorithm branch and terminate? | Inputs, operations, decisions, loop bounds, outputs/errors |

## Data

| Profile | Question answered | Required semantics |
|---|---|---|
| `erd` | What entities and relationships define the data model? | PK/FK fields, cardinality, optionality, associative entities |
| `etl-elt` | Where and when is data transformed? | Sources, landing, transformations, targets, orchestration, quality checks |
| `batch-pipeline` | How does scheduled/bounded data move? | Batch boundaries, schedules, checkpoints, retries, outputs |
| `streaming` | How does continuous event data move? | Producers/topics/consumers, async edges, partitions/windows/state where relevant |
| `lineage` | Which assets derive from which sources? | Dataset-level direction, transform/job, ownership, sensitivity when relevant |
| `lakehouse-medallion` | How does quality evolve across lakehouse layers? | Bronze/silver/gold responsibilities, transforms, consumption, governance |

## Delivery and operations

| Profile | Question answered | Required semantics |
|---|---|---|
| `ci-cd` | How does a change reach an environment? | Trigger, build/test, artifact, approvals, deployment/release, rollback |
| `devsecops` | Where are security controls in delivery? | SAST/SCA/secrets/IaC/container checks as evidenced, policy gates, exceptions |
| `observability` | How are telemetry and operational feedback produced? | Logs, metrics, traces, collection, storage/query, alerts, operators |
| `incident-response` | How is an incident detected and resolved? | Detect, triage, contain, recover, communicate, review; clear ownership lanes |

## Security

| Profile | Question answered | Required semantics |
|---|---|---|
| `trust-boundary` | Where does trust change? | Explicit trust zones, crossing flows, controls, sensitive assets |
| `zero-trust` | Where are identity and policy evaluated for each access? | Subject/workload identity, policy decision/enforcement, resource, telemetry |
| `auth-flow` | How is authentication/authorization performed? | Client, IdP/authorization server, tokens/codes, validation, protected resource |
| `threat-model` | What threatens assets and how is risk mitigated? | Assets, entry points, trust boundaries, threats, mitigations, residual risk |
| `data-classification` | How is data categorized and handled? | Classification levels, examples, storage/transfer/use controls, ownership |

## AI and ML

| Profile | Question answered | Required semantics |
|---|---|---|
| `ai-solution-overview` | How does the AI capability fit into the product/system? | User/product path, AI components, data, model/provider boundary, guardrails |
| `ml-lifecycle` | How does a model move from data to retirement? | Data, experiment/train, evaluate, register, deploy, monitor, retrain/retire |
| `mlops` | How is ML delivery automated and governed? | Feature/data pipelines, experiment tracking, registry, CI/CT/CD, serving, drift |
| `rag` | How does indexed knowledge ground generation? | Offline ingest/chunk/embed/index and online retrieve/rerank/generate paths |
| `agentic-rag` | How does an agent plan/tool-use while grounding in retrieved knowledge? | RAG paths plus agent state, tools, policy, stop/fallback, evidence return |
| `agent-orchestration` | How do agents delegate, hand off, and use tools? | Orchestrator/router, agents, tool boundaries, handoff/state, authority/failure |
| `inference-trace` | What happens during one inference request? | Ordered preprocessing, retrieval/tool calls, model call, guardrails, response/telemetry |
| `eval-observability` | How is AI quality measured in development and production? | Datasets/traces, evaluators, metrics, human review, feedback/drift/action |
| `ai-governance` | Who controls AI risk and lifecycle decisions? | Use cases/models/data, owners, policy/control, evidence, approval, monitoring |

## Product and UI

| Profile | Question answered | Required semantics |
|---|---|---|
| `user-flow` | How does a user reach a goal? | Entry, screens/actions, decisions, success/failure/recovery |
| `sitemap` | How is information organized? | Root, hierarchy, cross-links only when meaningful |
| `wireframe` | What is the interface structure? | Regions, components, interaction affordances, responsive assumptions |
| `service-blueprint` | How do customer actions and backstage operations align? | Customer/frontstage/backstage/support lanes, evidence, handoffs, failure points |

## Split rather than overload

Create multiple linked diagrams when one canvas tries to answer more than one of these: structural decomposition, runtime placement, one-request behavior, data lineage, security control, or operating lifecycle. Reuse stable model IDs and clearly label viewpoint/scope.
