# Software, enterprise, runtime, and cloud notation

## C4 views

Use C4 levels consistently. A context view contains people and software systems; a container view contains deployable/runnable units; a component view focuses inside one container. Do not mix classes, pods, database tables, and enterprise capabilities as peers.

Each focal element needs a name, type, responsibility, and—at container/component level—technology when known. Relationship labels are active verbs plus useful protocol/data, such as “submits order · HTTPS/JSON.” Boundary names should identify system/organization/container ownership.

## Dependency and UML class views

Dependency direction means “source depends on target.” If the reader instead needs runtime request direction, use integration/request-trace. Surface cycles deliberately; do not disguise them with symmetric lines.

For UML class, use compartments (`fields`) and established arrows. Put multiplicity on relationship labels. Avoid listing every trivial accessor; show members relevant to the design question.

## Enterprise views

Capabilities describe what, not organizational units or applications. Value streams describe value stages, not implementation tasks. If capabilities, organizations, processes, and systems appear together, separate them into layers and label the mapping semantics.

## Deployment and cloud

Distinguish logical software from runtime placement. Boundaries should communicate environment, region/zone, account/subscription/project, VPC/VNet, cluster, or namespace. Do not use cloud logos as generic decoration; each mark represents an actual evidenced service.

Show network direction, protocol/port, exposure, load balancer/gateway, and trust crossing when the question depends on them. Use separate arrows for request and response only when asymmetry matters; otherwise label one request edge without pretending it represents two independent operations.

## Kubernetes

Keep platform layers clear:

- cluster and namespace boundaries;
- ingress/gateway/service discovery;
- workload controllers and pods only at the requested depth;
- config, secret, identity, network policy, persistent volume, and external dependency when relevant.

Do not render every replica. Show desired multiplicity as metadata unless replica-level failure is the topic.

## Integration

Label synchronous vs asynchronous exchange. For async integration, show producer → broker/topic → consumer, event name/payload, and ownership. For API integration, show client → gateway/API → service, protocol, auth/policy boundary, and failure/timeout only when relevant.
