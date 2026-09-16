# Production Prompt

**Selected:** Prompt V2 · **Selected by:** TASK-27 · **Frozen:** 2026-09-14

| File | Role |
|---|---|
| [`prompt_production.md`](prompt_production.md) | The production prompt. Byte-identical copy of [`../v2/prompt_v2.md`](../v2/prompt_v2.md) as evaluated. |
| [`evaluation_thresholds.json`](evaluation_thresholds.json) | The threshold values **used during the TASK-27 evaluation**, preserved so the scores can be reproduced. **Not production-calibrated.** See §Thresholds. |
| [`MANIFEST.sha256`](MANIFEST.sha256) | SHA-256 of the frozen copies and their evaluated sources. |
| [`verify_production.py`](verify_production.py) | Confirms nothing has drifted. Exit 0 = intact. |

Selection evidence: [`../evaluation/RESULTS.md`](../evaluation/RESULTS.md).
Rubric: [`../evaluation/rubric.md`](../evaluation/rubric.md).

## Why this is a copy rather than a pointer

A pointer to `../v2/prompt_v2.md` would let an edit to V2 silently change what
production runs, and the TASK-27 scores would quietly stop describing it. The
copy plus manifest makes drift detectable instead of invisible.

```bash
python3 prompts/production/verify_production.py
```

Checks each frozen file against its recorded hash, and the frozen copy against
its evaluated source. Any edit to either — down to a trailing newline — fails.

## Rules

1. **Do not edit `prompt_production.md`.** It is the artefact TASK-27 scored.
2. **Do not edit `../v2/prompt_v2.md` either.** It is the evaluated source, and
   the manifest pins it too.
3. **Improvements become `prompts/v3/`**, evaluated with the same rubric against
   the same fixtures, after which this directory is re-pointed. Two known defects
   are already queued for v3 — see `RESULTS.md` §4.
4. **Thresholds are not calibrated.** See §Thresholds below.

## Thresholds

> [!IMPORTANT]
> **`evaluation_thresholds.json` does not contain production-calibrated values,
> and selecting this prompt for production did not calibrate them.**

The file exists for one reason: Prompt V2 cannot be executed without concrete
numbers, so the TASK-27 evaluation had to run with *some* values. Those values
are preserved here **only so the evaluation can be reproduced** — rendering the
prompt exactly as it was rendered when it was scored.

What they are and are not:

| | |
|---|---|
| **Are** | The exact values used to score V1 and V2, kept identical across both so the comparison measured the prompt and not a threshold change |
| **Are not** | Calibrated, empirically justified, or recommended for real detections |
| **Chosen for** | Placing the test fixtures on both sides of every decision boundary, so each branch of the prompt was exercised |
| **Source of truth** | [`docs/llm_scope_and_constraints.md`](../../docs/llm_scope_and_constraints.md) §5 (TASK-24), which defines these parameters and deliberately leaves their values **unset** |
| **Still pending** | Final calibration, blocked on TASK-18 (production model selection) and TASK-23 (matching accuracy) |

**Before this prompt processes real vehicle images, the thresholds must be
calibrated.** Running it on production data with these values means reporting
and suppression decisions rest on numbers picked to exercise test branches.

Recalibration replaces this file, and requires re-running the TASK-27 evaluation
— a threshold change changes report content, so the stored scores would no longer
describe the prompt's behaviour.

## A note on the frozen prompt's internal link

`prompt_production.md` refers to `test_thresholds.json` in its header. That link
points at the sibling of its **evaluated source**,
[`../v2/test_thresholds.json`](../v2/test_thresholds.json), which is unchanged
and still present. The frozen copy was deliberately **not** edited to update the
link: it is the artefact TASK-27 scored, and editing it — even a link — would
break the guarantee that production runs exactly what was evaluated.

## Use

```bash
python3 prompts/v2/render_prompt.py ../v1/fixtures/f01_high_confidence_single.json
```

`render_prompt.py` renders the evaluated V2 source, which the manifest pins to
the frozen copy. TASK-29 should load from this directory and run the verifier in
CI so a drifted prompt fails the build rather than reaching a report.
