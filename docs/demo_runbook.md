# Qaddir MVP Demo Runbook

Operational guide for presenting the Qaddir MVP (TASK-34). It covers startup,
the agreed demo images, what to say about each result, and the fallback path if
live inference fails.

The demo shows the real pipeline: image validation, damage and vehicle-part
detection, damage-to-part association, verification, and the report gate. It
does **not** show a generated LLM report — see [Why the report is Blocked](#why-the-report-is-blocked).
There are no cached or simulated results; every result on screen comes from
live inference.

## 1. Before the presentation

### Configuration

Copy `.env.example` to `.env` at the repository root and set only the
computer-vision entries. Paths are relative to the repository root.

| Variable | Value used for the tested demo run |
|---|---|
| `QADDIR_DAMAGE_MODEL_PATH` | `models/weights/qaddir_damage_best.pt` (Exp7 YOLO11m) |
| `QADDIR_PART_MODEL_PATH` | `notebooks/weights/carparts_yolo11n_wheel_fixed_v3_best.pt` |
| `QADDIR_CV_CONFIDENCE` | `0.25` |
| `QADDIR_CV_IMAGE_SIZE` | `640` |
| `QADDIR_CV_DEVICE` | `cpu` |

Leave `OPENAI_API_KEY`, `QADDIR_LLM_MODEL` and all five `QADDIR_T_*`
thresholds **empty**. Do not fill the thresholds with the test values from
`prompts/production/evaluation_thresholds.json`; that file is explicitly
labelled test-only and uncalibrated. Never commit `.env`.

### Start the backend

From the repository root:

```bash
source .venv/bin/activate
uvicorn qaddir_api.main:app --app-dir backend --env-file .env --reload
```

Confirm health at `http://localhost:8000/api/v1/health`. Expected for the demo:

| Component | Expected state |
|---|---|
| `cv` | ready |
| `verification`, `prompt`, `llm` | not ready (thresholds uncalibrated, no LLM configured) |
| overall `status` | `configuration_required` |

The first health request loads both models and can take several seconds; later
requests are fast.

### Start the frontend

In a second terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`. The intake card badge reads **Setup required**;
"View pipeline readiness" shows CV as Ready and the other components as Pending.
This is expected.

`next dev` rewrites `frontend/next-env.d.ts`. Do not commit that change.

### Dry run (5 minutes before)

1. Run primary image 1 end to end and confirm the overlay and damage cards appear.
2. Keep the demo images in one folder that is quick to reach from the file picker.
3. Keep this runbook open on a second screen.

## 2. Demo images

All images come from the CarDD YOLO **test split** (`images/test/`). The dataset
is not stored in this repository; see [`cardd_data_card.md`](cardd_data_card.md).

### Primary order

| # | File | Expected result | Point to make |
|---|---|---|---|
| 1 | `001493.jpg` | 4 damage detections: dent 85.5% → back bumper; scratch 70.7% → front door; crack 36.1% → front door; scratch 30.5% → back bumper. 10 vehicle parts. **Manual review**, report **Blocked**. | Multiple findings, each linked to a part by box overlap. Low-confidence detections are shown, not hidden. "Tied overlap score" badges show where more than one part fits equally. |
| 2 | `000090.jpg` | Glass shatter 92.0% → front glass, but part confidence only 27.9%. 2 parts. **Manual review**, report **Blocked**. | Strong damage detection with a weak part detection. The system surfaces the low part confidence instead of hiding it, which is why a human reviewer stays in the loop. |
| 3 | `000012.jpg` | Tire flat 95.0% → wheel. 5 parts. **Rejected**: the damage also overlaps the front bumper and back door, which are incompatible with a flat tire. Report **Blocked**. | Verification rejects contradictory evidence before anything could reach a language model, even when the main finding is correct. |

### Backup images

Chosen after running all 320 test-split images through the live pipeline (0
failures). Each has one clear, high-confidence detection linked to a plausible
part.

| File | Expected result |
|---|---|
| `001524.jpg` | Dent 88.7% → back door (part 85.8%). 3 parts. Manual review, report Blocked. |
| `000233.jpg` | Glass shatter 95.7% → front glass (part 80.3%). 3 parts. Manual review, report Blocked. In the overlay, the damage label sits under the part label; the damage card shows it clearly. |
| `000988.jpg` | Scratch 86.1% → front bumper (part 91.1%). 8 parts. Manual review, report Blocked. |

Confidence values can shift slightly if models, inference settings or
dependencies change. Re-run the dry run after any such change.

## 3. What to say

### Why the report is Blocked

> Production confidence thresholds are intentionally uncalibrated, so verification
> prevents unverified findings from reaching the language model. The CV findings
> stay on screen for human review; nothing is generated from evidence that has not
> passed verification.

Supporting points:

- Threshold values are a calibration decision that depends on final model and
  matching accuracy (`docs/llm_scope_and_constraints.md` §5). They are left unset
  on purpose rather than guessed.
- When enabled, the language model receives **verified structured CV data only**.
  It never sees the image.

### Wording to avoid

- Do not describe severity, repair needs, repair cost, cause of damage, or
  roadworthiness. The system does not assess them.
- If an image returns no damage detections, say "the pipeline returned no damage
  detections", never "the vehicle has no damage".
- The overlap score is box coverage, not a probability. Call it an overlap score.

## 4. Fallback path

If live inference fails during the presentation, work down this list and stop at
the first step that works:

1. **Refresh once.** Reload the page, select the image again and press
   Start assessment.
2. **Verify backend health.** Open `http://localhost:8000/api/v1/health`. If it
   does not respond, restart the backend (section 1) and check that `cv` is ready.
3. **Use a backup image** from section 2.
4. **If inference is still unavailable,** present the already-tested workflow
   and results from this runbook (section 2) and explain the architecture:
   image validation → damage and part detection → damage-to-part association →
   verification → report gate → human review. Do not substitute fabricated
   results or a written-up report.

### Messages the presenter may see

| On screen | Meaning | Action |
|---|---|---|
| "Assessment service unreachable" | Frontend cannot reach the backend | Step 2 |
| "CV pipeline not configured" | Model paths or CV settings in `.env` are wrong or missing | Check `.env`, restart backend |
| "Assessment timed out" | No response within 3 minutes | Step 2, then a backup image |
| "Image could not be used" | Wrong format, over 10 MB, or unreadable file | Choose a different image |
| Readiness badge "API offline" | Backend was down when the page loaded | Start backend, then refresh |
