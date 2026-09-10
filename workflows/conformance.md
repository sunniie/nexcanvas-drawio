# Cross-agent conformance workflow

Use this workflow to measure whether a host executes the shared NexCanvas skill,
not to create a normal user diagram. Read ADR 0009 and `docs/conformance.md`
before publishing a result.

## 1. Inspect the host

Run `nexcanvas conformance doctor`. Availability only means that a compatible
executable is visible locally; it does not prove conformance.

## 2. Prepare an immutable run pack

```bash
nexcanvas conformance prepare <case-id> --host <host-id> --output <run-pack>
```

The pack binds the exact corpus case, adapter, and shared `SKILL.md` by SHA-256.
Do not edit `request.json` or `PROMPT.md` after preparing it.

## 3. Execute in the named host

Start a fresh host session, submit `PROMPT.md`, and retain the transcript or task
export. The host must create the complete NexCanvas project in the pack's
`project/` directory. Do not repair another host's output before evaluation.

Fill `execution.template.json`, rename it to `execution.json`, and hash the raw
host evidence file. Record concrete `hostVersion` and `surface` values. A generic
claim such as "Agent Skills" is insufficient.

## 4. Evaluate without subjective substitutions

```bash
nexcanvas conformance evaluate <run-pack>/request.json \
  --project <run-pack>/project \
  --mode observed \
  --execution <run-pack>/execution.json \
  --output <run-pack>/result.json
```

The evaluator measures semantics, evidence, assets, routing, and completed
delivery gates. Every dimension must pass. Use `--mode fixture` only while
testing the evaluator; fixture output can never verify a host.

## 5. Publish the truthful matrix

```bash
nexcanvas conformance report <run-pack>/result.json \
  --output host-matrix.json \
  --markdown host-matrix.md
```

Publish raw observed results with the matrix when privacy and licensing permit.
Redact secrets before recording evidence, but never replace evidence with a prose
summary. Re-run a case whenever its skill, adapter, or corpus digest changes.
