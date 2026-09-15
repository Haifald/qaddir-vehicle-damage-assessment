# Branch and Integration Review

Reviewed on 2026-09-14 after refreshing remote references. No branch was merged.

## Available branches

| Branch | Head | Role |
|---|---|---|
| `main` | `41625dc` | CV notebooks, experiment evidence, reference extraction, and application work |
| `codex/safe-integration` | `41625dc` plus uncommitted application work | Dedicated branch for the immediate application integration safeguards |
| `origin/Ruba` | `df1720e` | Current remote LLM branch; merges `main` and retains the LLM work and TASK-28 review |
| local `Ruba` | `7a7a123` | Stale local pointer at the last LLM implementation commit |

The remote branch includes `main`, so current `main` is the merge base and
`origin/Ruba` is 13
commits ahead with no `main`-only commits. The LLM scope document and frozen
production prompt have identical Git object hashes at local `Ruba` and
`origin/Ruba`, confirming that the merge did not alter them. Retired remote
branches were removed by the refresh and are not current integration targets.

## What exists on `Ruba`

The LLM work is a prompt specification and evaluation suite, not an API client:

- `docs/llm_scope_and_constraints.md` defines the LLM as a transcription and
  presentation layer with strict hallucination constraints.
- `prompts/v1/` and `prompts/v2/` contain fixtures, expected outputs, prompt
  renderers, and adversarial hardening cases.
- `prompts/evaluation/` contains the comparison rubric and scores.
- `prompts/production/prompt_production.md` is a frozen, byte-identical copy of
  Prompt V2. It must not be edited in place.
- `prompts/production/evaluation_thresholds.json` contains test-only values. The
  branch explicitly says they are not calibrated production policy.
- `src/qaddir/llm/__init__.py` is only a package marker. There is no provider SDK,
  backend route, or executable report service on that branch.
- TASK-28 records that Prompt V2 was evaluated only on Claude Sonnet 5
  (`claude-sonnet-5`). The application's OpenAI gateway must be evaluated with
  its exact configured model before presentation use.

### Current LLM input

The current provisional JSON boundary is:

```text
image: { id, usable, quality_note }
damage_detections[]: { id, class, confidence }
part_detections[]: { id, class, confidence }
associations[]: { damage_id, part_id, confidence, alternatives[] }
```

Damage classes are the fixed six-class CarDD taxonomy. Part classes are the
fixed 13-class merged Carparts-Seg taxonomy. Damage, part, and association
confidence values are independent.

### Current LLM output

Prompt V2 produces plain text with one of four templates: standard preliminary
assessment, no findings, unusable image, or cannot report. Reportable detections
are written one per sentence. Low-confidence and unrecognised detections go to a
labelled appendix. The prompt forbids severity, repair, cost, safety, liability,
cause, timing, and aggregate vehicle-condition claims.

## What exists on `main`

`main` contains training and evaluation notebooks for both CV tracks. The README
records a selected vehicle-part model named
`carparts_yolo11n_wheel_fixed_v3_best.pt`, but that trained file is not committed.
The damage track has experiments but no selected production model. The two
tracked `.pt` files are downloaded generic Ultralytics starter/AMP-check weights,
not Qaddir production checkpoints.

Before this application work, `main` had no frontend, API, CV inference module,
verification layer, damage-to-part service, or LLM provider client.

## Integration decision

`Ruba` was not merged and no frozen prompt artifact was copied or modified.
Although the current remote branch is a clean superset of committed `main`, this
application work is uncommitted and overlaps the
README and `.gitignore` files changed on `origin/Ruba`; merging mid-implementation
would therefore be unnecessary and risk avoidable conflicts. Copying the
production prompt into `main` would duplicate a frozen teammate-owned artifact
and weaken its manifest guarantee.

The application instead loads the exact path
`prompts/production/prompt_production.md` at runtime. While that file is absent,
the health endpoint marks the prompt and LLM components unavailable. After the
team reviews and integrates `Ruba`, the app will consume the original frozen
file without modification.

## Remaining integration work

1. Select and export the production damage-model checkpoint.
2. Place both trained checkpoints outside Git and configure their paths.
3. Quantitatively validate or replace the provisional box-overlap association
   baseline in `backend/qaddir_api/matching.py`.
4. Calibrate all five confidence thresholds using production-model and matching
   evidence. Do not reuse the prompt-evaluation fixture thresholds as policy.
5. Review and integrate `Ruba` through the normal pull-request process.
6. Configure an approved OpenAI model and API key, re-evaluate the frozen prompt
   on that exact model, then run end-to-end evaluations.
