# Support

Use the channel that matches the request:

- reproducible defect: open a **Bug report**;
- poor or ambiguous rendered output: open a **Diagram quality report**;
- proposed capability or integration: open a **Feature proposal**;
- suspected vulnerability: follow [`SECURITY.md`](SECURITY.md), never a public issue;
- general usage question: open a GitHub issue with the `question` label.

Include the NexCanvas version, agent host, operating system, Python version,
Draw.io availability, command or prompt, and the smallest non-sensitive artifact
bundle that reproduces the problem. Remove credentials and private source content.

## Supported release lines

The latest `1.x` minor release receives fixes. The previous `1.x` minor receives
security fixes for at least 90 days after the next minor release. Pre-`1.0`
technical previews and arbitrary commits are unsupported unless a release note
explicitly says otherwise.

Support covers the runtime and persisted contracts listed in the
[compatibility matrix](docs/compatibility.md). Agent-host discovery and model
behavior are covered only when the [host conformance matrix](docs/host-capability-matrix.md)
contains current observed evidence.

Maintainers triage complete reports as soon as practical. Critical data-loss or
security issues take priority over visual refinements and feature proposals.
Published roadmap items and unreleased ideas are not commitments.
