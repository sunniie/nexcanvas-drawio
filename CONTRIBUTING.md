# Contributing to NexCanvas

Thank you for helping improve evidence-grounded, editable technical diagrams.
Contributions are welcome as focused issues, test cases, documentation, bug fixes,
diagram profiles, asset providers, QA rules, and implementation changes.

## Before opening a change

1. Search existing issues and pull requests.
2. For a substantial contract or architecture change, open a proposal issue first.
3. Keep one pull request focused on one reviewable outcome.
4. Do not include credentials, private repositories, confidential diagrams, or
   unlicensed assets in fixtures.

## Local validation

NexCanvas core development requires Python 3.10 or newer and uses the standard
library. Draw.io Desktop is optional for structural development but required for
claiming rendered visual verification.

From the repository root, run:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/test_drawio_qa.py -v
python scripts/validate_skill.py
python scripts/validate_conformance.py
nexcanvas doctor
python scripts/package_smoke.py
```

Validate tracked reference projects:

```bash
nexcanvas postflight examples/v2-rag-reference
nexcanvas postflight examples/v3-dense-industrial-ai
nexcanvas postflight examples/v4-hub-spoke-industrial
nexcanvas postflight examples/v5-multi-agent-workflow
```

## Branch and commit conventions

Create a short-lived branch from current `main`:

```text
feat/semantic-diff
fix/connector-routing
docs/asset-policy
test/dense-fan-in
refactor/package-layout
chore/release-config
```

Pull-request titles use Conventional Commit form because the squash-merge title
feeds release automation:

```text
feat(sync): add a semantic repository diff
fix(qa): reject ambiguous same-port relays
docs(contributing): explain asset provenance evidence
feat(schema)!: introduce semantic model V3
```

Branches are deleted after merge. `main` is the only permanent branch until a
supported release line genuinely requires a maintenance branch.

## Pull-request requirements

Every pull request must:

- explain the user-visible problem and chosen solution;
- identify public-contract or schema impact;
- include meaningful tests for changed behavior;
- keep all existing tests green;
- update documentation and migrations when required;
- avoid unrelated generated files or refactors;
- pass the stable CI quality gate.

Diagram, layout, connector, or visual QA changes must also include a minimal
fixture and before/after previews where the visual effect is material. The PR must
state whether Draw.io rendering was actually performed and visually inspected.

Asset contributions must record the exact product, owner, source URL, terms,
version, local path, and checksum. Never add an approximate neighboring product
logo as a substitute.

## Review principles

Reviews prioritize semantic correctness, evidence quality, editability,
portability, deterministic enforcement, and rendered clarity. XML validity alone
does not establish visual quality.

Maintainers may request that a large proposal be split into smaller pull requests.
Incomplete experimental behavior should remain behind an explicit experimental
interface and must not silently change stable output.

## Licensing

By submitting a contribution, you agree that it is licensed under the repository's
[MIT License](LICENSE). Third-party marks and assets remain subject to their
owners' licenses and trademark policies.
