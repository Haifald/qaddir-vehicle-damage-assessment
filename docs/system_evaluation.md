# TASK-35 — Integrated End-to-End System Evaluation

Consolidated scorecard for the Qaddir MVP, from image input through the report
gate, on held-out CarDD test images that were never used for training or model
selection.

| | |
|---|---|
| **Evaluation script** | [`scripts/evaluate_system.py`](../scripts/evaluate_system.py) |
| **Machine-readable results** | [`evaluation/summary.json`](evaluation/summary.json) |
| **Per-image predictions** | [`evaluation/predictions.jsonl`](evaluation/predictions.jsonl) |
| **Matching reference sheet** | [`evaluation/matching_reference_sample.csv`](evaluation/matching_reference_sample.csv) (awaiting human labels) |
| **Damage model** | Exp7 YOLO11m · `qaddir_damage_best.pt` · sha256 `b86d95d6cc207ae4…` |
| **Part model** | YOLO11n-seg · `carparts_yolo11n_wheel_fixed_v3_best.pt` · sha256 `46c0600fe767a68a…` |
| **Inference settings** | confidence 0.25 · image size 640 · CPU |
| **Thresholds / LLM** | Uncalibrated · the language model was not called |

> [!IMPORTANT]
> **No tuning decision may be made from these results.** They come from the test
> split. Threshold calibration, compatibility-rule changes and confidence changes
> recommended in §8 must be developed on the validation split and confirmed here
> only once.

## Scorecard

| Area | Measure | Result | Status |
|---|---|---|:--:|
| Damage detection | Box mAP50 / mAP50-95, 222 held-out images | **0.731 / 0.533** | Measured |
| Damage detection | Precision / recall at the deployed operating point (IoU 0.5) | **0.541 / 0.684** | Measured |
| Damage detection | Labelled images with at least one correct detection | **206 / 222 (92.8%)** | Measured |
| Vehicle-part model | Mask mAP50-95 on its own locked test split | **0.707** (notebooks 09–10) | Carried forward |
| Damage-to-part matching | Damages linked to a part | **763 / 820 (93.0%)** | Measured |
| Damage-to-part matching | **Accuracy** | **Not measured — verified part ground truth is unavailable** (§3) | **Gap** |
| Verification | Records eligible for the LLM | **0 / 311** (thresholds uncalibrated) | Measured |
| Verification | Records rejected as contradictory | **112 / 311 (36.0%)** — 78 of 79 labelled rejections contain a correct detection | Measured · **key finding** |
| LLM report quality | Hallucinations / omissions on hand-written fixtures, Claude Sonnet 5 | **0 / ~29 claims**; 8 / 11 reports fully supported | Carried forward (TASK-27/28) |
| LLM report quality | **On real records from unseen images** | **Not measured** — no record reached the LLM | **Gap** |
| End to end | Pipeline failures | **0 / 311** | Measured |
| End to end | Warm latency per image, p50 / p95 | **107.7 ms / 115.1 ms** | Measured |
| End to end | Invalid and non-vehicle inputs handled without crash | **4 / 4** | Measured |
| End to end | **Image → generated report** on unseen data | **0 / 311** reports generated | **Gap** |

**Verdict.** The CV and verification path is robust and fast on unseen images,
and its detection quality is consistent with the recorded test results. The full
image-to-report path cannot yet be evaluated end to end: thresholds are
uncalibrated, matching accuracy has no reference data, and no real record has
reached the language model.

## 1. Data

| | Count |
|---|--:|
| Image files in the local CarDD test split | 320 |
| Byte-identical duplicate downloads skipped (`…(1).jpg`) | 9 |
| **Unique images run end to end** | **311** |
| Of those, with YOLO box labels (used for detection metrics) | **222** |
| Without a local label file (pipeline measures only) | 89 |

- The official CarDD test split has 374 images; the local copy is incomplete,
  so detection metrics cover **222 / 374 (59%)** of it.
- The local test images share no filenames with the local train or validation
  splits.
- Label class order matches the model after display-label normalisation
  (`glass shatter` → `glass_shatter`, and so on); the script refuses to compute
  mAP otherwise.

## 2. Damage detection

### 2.1 Dataset-level accuracy

Standard Ultralytics evaluation (confidence 0.001) on the 222 labelled images,
compared with the one-time notebook test run on all 374 images.

| Metric | This run (222 images) | Notebook test (374 images) |
|---|--:|--:|
| Precision | 0.757 | 0.733 |
| Recall | 0.700 | 0.657 |
| mAP50 | 0.731 | 0.685 |
| mAP50-95 | 0.533 | 0.503 |

| Class | mAP50-95, this run | Notebook test |
|---|--:|--:|
| `tire_flat` | 0.834 | 0.836 |
| `glass_shatter` | 0.816 | 0.817 |
| `lamp_broken` | 0.699 | 0.598 |
| `dent` | 0.350 | 0.295 |
| `scratch` | 0.312 | 0.272 |
| `crack` | 0.189 | 0.199 |

Per-class ranking is unchanged. The slightly higher overall figures reflect the
subset, not a model change: the checkpoint hash matches the committed Exp7 model.

### 2.2 At the deployed operating point

What the application actually shows: confidence ≥ 0.25, a prediction counts as
correct at IoU ≥ 0.5 with the right class.

| Class | Ground truth | Predictions | Precision | Recall | F1 |
|---|--:|--:|--:|--:|--:|
| `glass_shatter` | 45 | 52 | 0.827 | 0.956 | 0.887 |
| `tire_flat` | 22 | 23 | 0.826 | 0.864 | 0.844 |
| `lamp_broken` | 34 | 40 | 0.725 | 0.853 | 0.784 |
| `dent` | 139 | 145 | 0.579 | 0.604 | 0.592 |
| `scratch` | 176 | 274 | 0.427 | 0.665 | 0.520 |
| `crack` | 34 | 35 | 0.457 | 0.471 | 0.464 |
| **All** | **450** | **569** | **0.541** | **0.684** | |

- **False positives concentrate in `scratch`:** 157 of 261 false positives.
- **Misses are localisation failures, not class confusion:** of 142 missed
  instances, 134 had no overlapping prediction and only 8 were found with the
  wrong class. Class-agnostic precision / recall is 0.554 / 0.700.
- 4 of 222 labelled images produced no damage detection at all.

## 3. Damage-to-part matching

### 3.1 Behaviour (all 311 images, 820 damage detections)

| Measure | Count | Share |
|---|--:|--:|
| Linked to a part | 763 | 93.0% |
| Not linked (no overlapping part) | 57 | 7.0% |
| With at least one alternative part | 530 | 64.6% |
| Leading part tied with an alternative | 77 | 9.4% |
| Median leading overlap score | 1.0 | |

Most damage boxes lie entirely inside a part box, and two-thirds also overlap a
second part. Overlap score is box coverage, not a probability; a median of 1.0
says nothing about whether the chosen part is correct.

### 3.2 Accuracy — not measured: verified part ground truth is unavailable

CarDD provides damage labels only; there are no vehicle-part labels for these
images. TASK-23 is closed on GitHub, but the repository contains no verified
reference sample or accuracy result, and the threshold files still list TASK-23
as pending. **No matching-accuracy figure can be reported without human
verification**, and this evaluation does not substitute model- or AI-generated
labels for one.

To close the gap, `evaluation/matching_reference_sample.csv` holds **60 correctly
detected damage instances** (10 per damage class, fixed seed) with the predicted
part and alternatives:

1. For each row, a reviewer opens the image, locates the damage box, and enters
   the correct part class in `reference_part_class` (a value from `PART_CLASSES`
   in `backend/qaddir_api/config.py`, or `none`), plus `reviewer`.
2. Re-run the script with `--matching-reference docs/evaluation/matching_reference_sample.csv`.
   Accuracy, per-class accuracy and every mismatch are added to `summary.json`.
   A sheet that already contains labels is never overwritten.

## 4. Verification and the report gate

| Outcome | Images |
|---|--:|
| `verified` | 0 |
| `manual_review` | 199 (64.0%) |
| `rejected` | 112 (36.0%) |
| Eligible for the LLM | **0** |
| Report `blocked` | 311 |

Every non-rejected record is held for manual review by `thresholds_not_calibrated`,
which is the intended fail-closed behaviour while thresholds are unset.

### 4.1 Key finding: contradiction rejections discard real damage

All 112 rejections come from the strict part-compatibility rule, which applies to
`glass_shatter`, `lamp_broken` and `tire_flat`:

| Cause | Images |
|---|--:|
| The **leading** part is incompatible (e.g. `lamp_broken` → `front_bumper`) | 59 |
| Only an **alternative** part is incompatible | 53 |

- **78 of the 79 rejected labelled images contain at least one correctly detected
  damage.** The rule is rejecting genuine evidence, not only bad detections.
- Incompatible alternatives are mostly geometric neighbours: lamps sit inside
  bumper and hood boxes, tyres overlap doors and bumpers. Their median overlap is
  0.16; 22% are below 0.05.
- The most frequent pairs are `lamp_broken` with `front_bumper` / `hood` /
  `back_bumper`, `glass_shatter` with `hood`, and `tire_flat` with `back_door` /
  `front_bumper` / `back_bumper`.

These are exactly the classes with the strongest detection accuracy (§2), so the
current rule removes the system's most reliable findings from the report path.
This is a policy and matching issue, not a detection issue. See §8.

## 5. LLM report quality

Carried forward from TASK-27 and TASK-28; **not re-measured here**. That evaluation
and the live backend are separate:

| | TASK-27/28 prompt evaluation | Live backend |
|---|---|---|
| Model | **Claude Sonnet 5** (`claude-sonnet-5`) | OpenAI Responses API, model set by `QADDIR_LLM_MODEL` (not configured) |
| Input | Hand-written structured fixtures | Verified records from the CV pipeline |
| Thresholds | Test-only placeholder values | Uncalibrated, so no record is eligible |
| Reports produced | 11 reviewed manually | **None** |

| Measure | Result |
|---|---|
| Hallucination rate | 0 / ~29 claims |
| Omission rate | 0 / ~29 claims |
| Claim-level defect rate (factual, misleading, traceability) | ~4 / 29 ≈ 14% |
| Reports with every claim supported | 8 / 11 |
| Adversarial fixtures handled (Prompt V2) | 4 / 4 |
| Severity, cause, cost, repair or safety language | Never produced, including when injected |

Limits that apply to every figure above:

- Inputs were **hand-written fixtures**, not records produced by the CV pipeline.
- One generation per fixture, English only, evaluated on **Claude Sonnet 5** only.
  The prompt has not been evaluated on the provider the backend is configured for
  (`docs/application_architecture.md`).
- Fixtures used the **test-only threshold values**, not calibrated ones.

In this evaluation no record was eligible, so report generation, the output guard
and grounding on real unseen data remain untested.

## 6. Runtime and robustness

Warm, in-process `AssessmentService.assess()` per image on a laptop CPU (Apple
silicon): validation, both models, association, overlay rendering, verification
and the report gate. HTTP transport is excluded.

| Measure | Value |
|---|--:|
| Model load and readiness check | 650 ms |
| Images completed / failed | 311 / 0 |
| Mean latency | 110.2 ms |
| p50 / p90 / p95 | 107.7 / 112.5 / 115.1 ms |
| Max (first image, warm-up) | 690.4 ms |

This agrees with the single-image TASK-30 profile (warm ≈ 112 ms). Report
generation time is not included because no report was generated.

| Probe | Outcome |
|---|---|
| Non-vehicle image (blank 640×640) | Structured response, 0 damage detections, `manual_review`, report `blocked` |
| Image below the 320 px minimum side | Marked unusable, not analysed, report `blocked` |
| Corrupt bytes | Controlled `invalid_image` rejection (HTTP 400 in the API) |
| Unsupported content type | Controlled `invalid_image` rejection |

The same non-vehicle input was also sent over HTTP to the running API (HTTP 200,
structured response, no traceback); see [`integration_testing.md`](integration_testing.md).

## 7. End-to-end outcome

| Stage | Images reaching the stage |
|---|--:|
| Validated and analysed | 311 |
| Verification passed (`verified`) | 0 |
| Report generated | 0 |

The system turns every unseen image into a structured, verifiable CV record with
no failures and sub-120 ms warm latency, and it withholds every report, as its
fail-closed design requires in the current configuration. Whether the complete
system produces accurate, grounded reports on real images is **not yet
established**.

## 8. Recommendations

In priority order. Each must be developed on validation data (§ note at top).

1. **Measure matching accuracy.** Complete the 60-row reference sheet with human
   reviewers and re-run with `--matching-reference`. This also unblocks
   `T_ASSOC_STATE` and `T_ASSOC_AMBIG`.
2. **Revisit contradiction handling before calibration.** Candidate options, to
   be compared on the validation split: treat an incompatible *alternative* as
   review-level instead of a rejection, or drop incompatible alternatives during
   association; separately review cases where a compatible part is present but
   not leading.
3. **Calibrate the five thresholds** on validation data once 1 and 2 are settled.
4. **Evaluate reports on real records.** With thresholds set, run the configured
   LLM (`--allow-llm`) on verified records from the validation split, review them
   against the TASK-28 rubric, then confirm once on this test set.
5. **Reduce `scratch` false positives** (157 of 261), e.g. a class-specific
   operating threshold chosen on validation data.
6. **Complete the test split.** Obtain the missing 152 labelled test images and
   re-run so detection metrics cover all 374.

## 9. Reproduce

From the repository root, with the backend dependencies installed and model paths
set in `.env`:

```bash
PYTHONPATH=backend python scripts/evaluate_system.py \
  --env-file .env \
  --images <CarDD_YOLO>/images/test \
  --labels <CarDD_YOLO>/labels/test \
  --data-yaml <CarDD_YOLO>/data.yaml \
  --out docs/evaluation \
  --map
```

- The language model is never called unless `--allow-llm` is passed.
- Outputs contain file names only; no absolute paths or secrets.
- Ultralytics automatic package installation is disabled for the run.
- A CPU run of 311 images plus the mAP pass takes about two minutes.

## Definition of Done

> A consolidated evaluation scorecard/report is produced using unseen data and
> includes the agreed CV, matching, LLM and end-to-end performance measures.

| Requirement | Status |
|---|---|
| Consolidated scorecard on unseen data | ✅ This document and `evaluation/summary.json` |
| CV measures | ✅ Measured on 222 held-out images |
| End-to-end performance measures | ✅ Reliability, latency and robustness on 311 images |
| Matching measures | ⚠️ Coverage and ambiguity measured; **accuracy not measured — verified part ground truth is unavailable** |
| LLM measures | ⚠️ Fixture evaluation on Claude Sonnet 5 carried forward; **not measured on real records or on the configured provider**, because no record is eligible while thresholds are uncalibrated |

**Status: partially met.** The scorecard, CV, end-to-end, verification and runtime
measures are supported by evidence on unseen data. Matching accuracy and live report
quality remain unavailable for the reasons above and are recorded as open gaps rather
than estimated.
