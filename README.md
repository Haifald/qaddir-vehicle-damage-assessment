<div align="center">

# Qaddir

**AI-Assisted Preliminary Vehicle Damage Assessment**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-CV%20experiments-yellow)]()
[![Notebooks](https://img.shields.io/badge/notebooks-Jupyter-f37626)](notebooks/)

Identify visible vehicle damage from photographs, locate the affected part, and
produce a structured preliminary report for human review.

</div>

---

## Contents

- [Concept](#concept)
- [How It Works](#how-it-works)
- [Damage Taxonomy](#damage-taxonomy)
- [Vehicle-Part Taxonomy](#vehicle-part-taxonomy)
- [Project Status](#project-status)
- [Results So Far](#results-so-far)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Roadmap](#roadmap)
- [References](#references)

---

## Concept

Assessing vehicle damage from photographs is manual, slow and inconsistent. The
same images can lead different assessors to different conclusions, and the work
does not scale to the volume of claims and inspections handled in practice.

Qaddir explores two questions:

1. Can computer vision reliably identify **what damage is visible** and **which
   vehicle part it affects**?
2. Can a language model turn those structured findings into a **readable
   preliminary report** without inventing anything the models did not detect?

The result is intended as an aid that a qualified person reviews and approves —
never a system that decides on its own.

## How It Works

```text
        vehicle image
              │
              ▼
   ┌──────────────────────┐        ┌──────────────────────┐
   │   damage detection   │        │ vehicle-part         │
   │   what & where       │        │ segmentation         │
   │   (CarDD)            │        │ (Carparts-Seg)       │
   │   ✅ trained          │        │ ✅ trained            │
   └──────────┬───────────┘        └──────────┬───────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
                  damage-to-part matching          ⬜ not started
                  e.g. scratch → front bumper
                              │
                              ▼
                      structured JSON              ⬜ not started
              damage type · part · confidence
                              │
                              ▼
                       language model              ⬜ not started
                              │
                              ▼
                   preliminary report
                  reviewed and approved
                       by a person
```

**The structured JSON is the boundary between the two components.** The language
model receives only what the vision models actually detected, so every statement
in the generated report traces back to a detection. This is what keeps the
report grounded rather than plausible-sounding.

Two datasets support the vision side, plus one external dataset merged into the
vehicle-part track:

| Dataset | Role | Scale |
|---|---|---|
| **CarDD** | Damage detection — 6 damage types | 4,000 images · 8,740 instances |
| **Carparts-Seg** | Vehicle-part segmentation — merged to 13 classes | 3,833 images |
| **Humans in the Loop** | External part data, audited and merged | 998 images · 9,189 polygons |

## Damage Taxonomy

Six damage classes, taken from CarDD without merges or exclusions, renamed to
snake_case for tooling compatibility. The ordering is **fixed**: it is written
into the dataset configuration and baked into any trained model.

| ID | Class | Instances | Share | Notes |
|:--:|---|--:|--:|---|
| 0 | `dent` | 2,543 | 29.1% | Panel deformed, finish largely intact |
| 1 | `scratch` | 3,595 | 41.1% | Surface finish only, panel undeformed |
| 2 | `crack` | 898 | 10.3% | Through-material split — smallest, hardest class |
| 3 | `glass_shatter` | 682 | 7.8% | Window glass only |
| 4 | `lamp_broken` | 704 | 8.1% | Light units, including the lens |
| 5 | `tire_flat` | 318 | 3.6% | Tyre only, not the rim |

Measured across all 8,740 annotated instances. Full definitions, boundary rules
and the CarDD label mapping live in the `Ruba` working branch
(`docs/damage_classes.md`) and will be published here once merged.

## Vehicle-Part Taxonomy

The original Carparts-Seg 23 classes were merged down to **13**. Direction-specific
doors, lights and mirrors were collapsed into general part classes, the ambiguous
`object` class was dropped, and the `trunk` / `tailgate` definitions were corrected
after a cross-dataset annotation review.

| ID | Class | Train instances | | ID | Class | Train instances |
|:--:|---|--:|---|:--:|---|--:|
| 0 | `back_bumper` | 935 | | 7 | `front_light` | 3,465 |
| 1 | `back_door` | 1,752 | | 8 | `hood` | 1,971 |
| 2 | `back_glass` | 939 | | 9 | `side_mirror` | 1,372 |
| 3 | `back_light` | 2,202 | | 10 | `trunk_or_tailgate` | 370 |
| 4 | `front_bumper` | 1,884 | | 11 | `truck_bed` | 121 |
| 5 | `front_door` | 1,973 | | 12 | `wheel` | 2,005 |
| 6 | `front_glass` | 1,904 | | | | |

Splits are built at **source-image level**, so augmented versions of one source
image can never cross a split boundary: 3,269 train / 561 validation / 554 test.

## Project Status

**Phase: computer-vision experiments.** Both vision models are trained. The
matching, LLM and interface layers have not been started.

The work runs as two parallel tracks, which is why the notebook numbering has
two `07`s and two `10`s — one of each per track.

### Damage detection track (CarDD)

| Notebook | Purpose | Status |
|---|---|:--:|
| `01_CarDD_Data_Analysis_EDAL.ipynb` | CarDD EDA: composition, imbalance, box geometry, spatial distribution, annotation quality | ✅ |
| `02_cardd_annotation_conversion_.ipynb` | CarDD COCO → YOLO segmentation conversion | ✅ |
| `07_cardd_baseline_model_.ipynb` | Baseline damage model (Experiment 1) | ✅ |
| `10_cardd_experiment_2.ipynb` | Experiment 2 — stronger augmentation, longer schedule | ✅ |

### Vehicle-part track (Carparts-Seg)

| Notebook | Purpose | Status |
|---|---|:--:|
| `03_carparts_preprocessing.ipynb` | Validation: splits, annotations, class balance, mask quality | ✅ |
| `04_carparts_cleaning_and_preparation.ipynb` | Cleaning, class merge to 13, leakage-safe source-level split | ✅ |
| `05_carparts_segmentation_baseline.ipynb` | YOLO11n-seg baseline fine-tune | ✅ |
| `06_external_carparts_data_audit.ipynb` | Audit of the external Humans in the Loop dataset | ✅ |
| `07_carparts_expanded_data_training.ipynb` | Expanded-data training; found trunk/tailgate class mismatch | ✅ |
| `08_carparts_corrected_augmentation_training.ipynb` | Corrected classes + controlled augmentation | ✅ |
| `09_carparts_wheel_fixed_baseline.ipynb` | Wheel-corrected baseline (`v3`) | ✅ |
| `10_carparts_manual_hyperparameter_tuning.ipynb` | Five-stage manual tuning, model selection, locked test evaluation | ✅ |

### Not started

Damage-to-part matching, the structured CV output schema, the language-model
component, the Streamlit prototype, and integrated end-to-end evaluation.

> **Note** — `docs/damage_classes.md`, the `src/qaddir/` package and
> `pyproject.toml` currently exist only on the `Ruba` branch and are not yet
> merged into `main`.

## Results So Far

### Vehicle-part segmentation — final model selected

The selected model is the wheel-fixed `v3` baseline
(`carparts_yolo11n_wheel_fixed_v3_best.pt`). Manual hyperparameter tuning
improved overall Mask mAP50-95 by only +0.0034 — inside the pre-agreed 0.005
practical tolerance — while *reducing* wheel performance, so the baseline was
kept.

The test split stayed locked throughout tuning and selection, and was evaluated
**once**, after the model was chosen:

| Metric | Validation | Test |
|---|--:|--:|
| Mask Precision | 0.894 | 0.838 |
| Mask Recall | 0.883 | 0.897 |
| Mask mAP50 | 0.935 | 0.906 |
| Mask mAP50-95 | 0.737 | 0.707 |
| Wheel Mask mAP50-95 | 0.618 | 0.611 |

`wheel` remains the weakest class, traced to known inconsistencies in wheel
annotations rather than to the training configuration.

### Damage detection — experiments in progress

| Metric | Exp 1 (baseline) | Exp 2 (augmentation) | Change |
|---|--:|--:|--:|
| Precision | 0.625 | 0.623 | −0.002 |
| Recall | 0.576 | 0.627 | **+0.051** |
| mAP50 | 0.587 | 0.633 | **+0.046** |
| mAP50-95 | 0.462 | 0.456 | −0.006 |

Experiment 2 is a **mixed result** — clearly better recall and mAP50, marginally
worse mAP50-95 — so no production damage model has been selected yet.

Per-class validation, Experiment 2:

| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|--:|--:|--:|--:|
| `dent` | 0.583 | 0.469 | 0.498 | 0.234 |
| `scratch` | 0.529 | 0.449 | 0.453 | 0.222 |
| `crack` | 0.259 | 0.158 | 0.116 | 0.045 |
| `glass_shatter` | 0.915 | 0.978 | 0.984 | 0.824 |
| `lamp_broken` | 0.586 | 0.837 | 0.835 | 0.624 |
| `tire_flat` | 0.869 | 0.871 | 0.914 | 0.786 |

The pattern is consistent and worth stating plainly: **discrete, high-contrast
damage is close to solved; diffuse surface damage is not.** `glass_shatter` and
`tire_flat` exceed 0.78 mAP50-95, while `crack` sits at 0.045 — it is the
smallest class, and the hardest to see.

## Repository Structure

```text
qaddir-vehicle-damage-assessment/
├── notebooks/                  Analysis, preparation and training
│   ├── 01,02,07,10_cardd_*     Damage detection track
│   ├── 03–10_carparts_*        Vehicle-part track
│   └── cardd_eda_extracted/    CarDD COCO annotation files
├── docs/
│   ├── cardd_data_card.md      CarDD data card
│   ├── references.md           External references
│   └── reference_pdf_extraction.md
├── references/                 Taqeem standards PDF + OCR-extracted text
├── scripts/
│   └── extract_reference_pdf.py
├── data/README.md              Required local dataset layout
├── requirements.txt
└── Qaddir-TaskPlan-Clear-Descriptions.xlsx    The 40-task project plan
```

| Location | Purpose |
|---|---|
| `notebooks/` | Exploration, data preparation, training and evaluation. Numbered in pipeline order, per track. |
| `docs/` | Recorded decisions, data cards and external references. |
| `references/` | The Taqeem professional-standards PDF and its reviewed OCR text, staged for the LLM/RAG work. |
| `scripts/` | Standalone utilities. |
| `data/` | Local datasets in a fixed layout. Contents excluded from Git; only the layout spec is tracked. |

## Getting Started

**Requirements:** Python 3.10 or later.

```bash
git clone https://github.com/Haifald/qaddir-vehicle-damage-assessment.git
cd qaddir-vehicle-damage-assessment

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Then open `notebooks/` and select the project virtual environment as the kernel.

The reference-extraction script additionally needs Tesseract OCR 5 with the
`ara` and `eng` language data — see
[`docs/reference_pdf_extraction.md`](docs/reference_pdf_extraction.md).

### Compute note

Training was run on Google Colab and Kaggle GPUs (Tesla T4), not locally. The
notebooks keep their outputs committed, so the recorded metrics are readable
without re-running them.

### Datasets

Datasets are **not** included in this repository. Place them locally following
[`data/README.md`](data/README.md):

```text
data/
├── cardd/{raw,processed}/
└── carparts/{raw,processed}/
```

CarDD is obtained from its authors, who provide a download link after a signed
licensing form — see [References](#references).

### Built With

`ultralytics` · `pycocotools` · `opencv-python` · `numpy` · `pandas` ·
`matplotlib` · `seaborn` · `Pillow` · `PyYAML` · `PyMuPDF` · `pytesseract` ·
`jupyter`

## Development Workflow

Work is organised as **40 tasks**, tracked as GitHub Issues (`TASK-01` to
`TASK-40`) and in the project plan spreadsheet. Each task records its epic,
owner, priority, dependencies and a Definition of Done.

| Epic | Tasks | | Epic | Tasks |
|---|:--:|---|---|:--:|
| Foundation | 5 | | LLM | 5 |
| Data Preparation | 6 | | Integration | 2 |
| CV Baseline | 4 | | MVP | 4 |
| CV Improvement | 5 | | Evaluation | 1 |
| Damage-Part Match | 3 | | Documentation | 5 |

Closed to date: TASK-01 through TASK-04 and TASK-06 through TASK-16.
TASK-05 (cross-domain feasibility spike) remains open and was taken out of
sequence.

**Branches**

| Branch | Role |
|---|---|
| `main` | Stable, reviewed work |
| `Ruba` | Active development branch |

**Conventions**

- A task is complete when its Definition of Done is objectively met — not when
  the code appears to work.
- Notebooks are numbered in pipeline order and keep their outputs committed, so
  results are visible without re-running them.
- Datasets are never committed; only the layout specification is tracked.
- Test splits stay locked until a model is selected on validation data.

## Roadmap

In dependency order:

1. **Run damage Experiment 3** (model size or training strategy) and **select the
   production damage model** — Experiment 2 was inconclusive.
2. **Error analysis** on the selected model, with correct and incorrect
   prediction examples, focused on `crack` and `scratch`.
3. **Measure the domain gap** — the part model trains largely on intact vehicles
   but must run on photographs of damaged ones (TASK-05, still open).
4. **Define the structured CV output schema** — the JSON contract between the
   vision models and the language model.
5. **Implement and evaluate damage-to-part matching.**
6. **Build the LLM layer** — role, scope, hallucination constraints, then prompt
   versions compared and one selected.
7. **Build the Streamlit MVP** and run integrated end-to-end evaluation.

## References

- **CarDD** — Wang, Li & Wu, *CarDD: A New Dataset for Vision-Based Car Damage
  Detection*, IEEE Transactions on Intelligent Transportation Systems,
  24(7):7202–7214, 2023. [doi:10.1109/TITS.2023.3258480](https://doi.org/10.1109/TITS.2023.3258480)
  · [project site](https://cardd-ustc.github.io/)
- **Professional Standards for Vehicle Damage Assessment** — Saudi Authority for
  Accredited Valuers (Taqeem). Staged locally in `references/`.
- Further references in [`docs/references.md`](docs/references.md).

---

## Disclaimer

This project is a proof of concept and **does not replace professional vehicle
assessment**. Its output is a preliminary aid for human review, not a final
decision.
