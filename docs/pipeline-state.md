# Deterministic pipeline state

`nexcanvas generate` turns NexCanvas delivery gates into one resumable state
machine. It operates on an authored project; it does not replace evidence
investigation, semantic modeling, asset selection, or visual judgment.

## Ordered stages

| Stage | Primary inputs | Outputs |
|---|---|---|
| `plan` | `diagram_model.json` | `reports/layout_brainstorm.json` |
| `build` | diagram model and effective asset content | editable `.drawio`, `reports/build.json` |
| `diagram-qa` | source, lock, model, assets, Draw.io, repository context | `reports/diagram_qa.json` |
| `render` | current Draw.io and export options | preview, `reports/render.json` |
| `visual-qa` | current preview and target dimensions | `reports/visual_qa.json` |
| `postflight` | all current contracts, QA, approval, assets, and repository context | `reports/postflight.json` |

Each stage stores a canonical `inputHash`, dependency output hashes, generated
file hashes, status, timestamps, and attempt count in `project_state.json`.
Absolute project paths are not stored in file records. Asset fingerprints use the
declared identity and actual local file content, while equivalent lifecycle
advances such as `Embedded` to `RenderVerified` do not cause false invalidation.

## Reconciliation and invalidation

At the start of a run, every stage is checked just before execution:

- a complete stage with matching inputs, dependencies, and output files is reused;
- changed inputs or dependencies mark that stage and downstream work stale;
- missing or externally edited output files also invalidate that stage and downstream work;
- a failed or stale stage is run again, while valid upstream work is preserved;
- `--restart` deliberately invalidates every stage but does not delete project files.

Changing the model therefore reruns layout, build, QA, render, approval, and
postflight. Changing only the preview invalidates render onward. Changing an
approval report invalidates visual QA and postflight. A later NexCanvas version is
also part of the stage fingerprint so compiler changes are never silently trusted.

## Visual-review boundary

The first successful generate pass renders a preview, writes a pending visual
report, sets project status to `awaiting-review`, and exits `3`. This is a
successful handoff to an external review gate, not completed delivery.

Only a second invocation with `--approve-visual`, a reviewer, and concrete notes
can complete `visual-qa`. The approval report contains the current artifact hash.
Postflight runs only after that stage is complete and rechecks the artifact hash.
An agent without image-view capability must leave the project awaiting review.

## Failure and resume

An exception or unavailable runtime is recorded on the active stage and exits
`2`. A QA gate that executes but does not pass is recorded as `failed` and exits
`1`. Rerun the identical command after correcting the input or runtime. NexCanvas
reuses valid upstream records and resumes at the first failed, stale, or pending
stage.

Automation should read the JSON result and `project_state.json`; it should not
infer completion from the presence of a `.drawio` or PNG alone.
