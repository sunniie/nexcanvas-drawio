# Visual benchmarks

NexCanvas visual benchmark suite `1.0` converts the project's reference quality
bar into a repeatable, hash-bound gate. It covers sparse, dense, cloud, AI,
sequence, data-flow, and lifecycle compositions.

```bash
nexcanvas benchmark validate
nexcanvas benchmark run
```

The release profile passes only when every case satisfies all four dimensions:

| Dimension | Evidence |
|---|---|
| Geometry | Draw.io overlap, route, terminal, connector-lane, and boundary checks |
| Text bounds | Label, caption, callout, and badge collision checks separated from structural errors |
| Perceptual proxies | PNG dimensions, ink coverage, and luminance entropy |
| Human review | Explicit approval whose stored SHA-256 matches the evaluated PNG |

Perceptual proxies detect blank, corrupt, implausibly sparse, or saturated
renders. They are not an aesthetic score. Human inspection remains mandatory
for a release-grade pass and must verify hierarchy, balance, legibility,
connector meaning, icon accuracy, and intentional composition at target size.

`--automated-only` is intended for deterministic CI diagnostics. It can report
`automatedPassed: true`, but deliberately leaves `passed: false`; CI automation
cannot manufacture human approval.

The tracked suite is [`benchmarks/suite.json`](../benchmarks/suite.json). Each
case binds a model, editable Draw.io baseline, rendered PNG, visual-review
record, semantic intent, and density range. Any changed render invalidates its
human approval until the new PNG is viewed and reviewed again.
