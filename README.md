<div align="center">

# Qaddir

**AI-Assisted Preliminary Vehicle Damage Assessment**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-dataset%20preparation-orange)]()
[![Notebooks](https://img.shields.io/badge/notebooks-Jupyter-f37626)](notebooks/)

Identify visible vehicle damage from photographs, locate the affected part, and
produce a structured preliminary report for human review.

</div>

---

## Contents

- [Concept](#concept)
- [How It Works](#how-it-works)
- [Damage Taxonomy](#damage-taxonomy)
- [Repository Structure](#repository-structure)
- [Project Status](#project-status)
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
   │   what & where       │        │ detection            │
   │   (CarDD)            │        │ (Carparts-Seg)       │
   └──────────┬───────────┘        └──────────┬───────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
                  damage-to-part matching
                  e.g. scratch → front bumper
                              │
                              ▼
                      structured JSON
              damage type · part · confidence
                              │
                              ▼
                       language model
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

Two datasets support the vision side:

| Dataset | Role | Scale |
|---|---|---|
| **CarDD** | Damage detection — 6 damage types | 4,000 images · 8,740 instances |
| **Carparts-Seg** | Vehicle-part detection — 23 part classes | 3,833 images |

> **Note** — This diagram is the target architecture. Only the data analysis and
> preparation stages exist today. See [Project Status](#project-status).

## Damage Taxonomy

Six damage classes, taken from CarDD without merges or exclusions, renamed to
snake_case for tooling compatibility. The ordering is **fixed**: it is written
into the dataset configuration and baked into any trained model.

| ID | Class | Share of instances | Notes |
|:--:|---|--:|---|
| 0 | `dent` | 29.1% | Panel deformed, finish largely intact |
| 1 | `scratch` | 41.1% | Surface finish only, panel undeformed |
| 2 | `crack` | 10.3% | Through-material split — smallest, hardest class |
| 3 | `glass_shatter` | 7.8% | Window glass only |
| 4 | `lamp_broken` | 8.1% | Light units, including the lens |
| 5 | `tire_flat` | 3.6% | Tyre only, not the rim |

Shares are measured across all 8,740 annotated instances. Full definitions,
boundary rules and the CarDD label mapping are maintained in the `Ruba` working
branch and will be published here once merged.

## Repository Structure

```text
qaddir-vehicle-damage-assessment/
├── notebooks/                  Analysis and preparation, numbered in pipeline order
│   ├── 01_cardd_data_analysis.ipynb
│   ├── 02_cardd_annotation_conversion.ipynb
│   ├── 03_carparts_preprocessing.ipynb
│   ├── 07_cardd_baseline.ipynb
│   └── cardd_eda_extracted/    CarDD COCO annotation files
├── docs/
│   └── references.md           External references
├── data/
│   └── README.md               Required local dataset layout
├── requirements.txt            Dependencies
└── Qaddir-TaskPlan-Clear-Descriptions.xlsx    The 40-task project plan
```

| Location | Purpose |
|---|---|
| `notebooks/` | Exploration, data preparation and reporting. Numbered in pipeline order. |
| `docs/` | Recorded decisions and external references. |
| `data/` | Local datasets in a fixed layout. Contents excluded from Git; only the layout spec is tracked. |

## Project Status

**Phase: dataset preparation.** No model has been trained yet.

| Notebook | Purpose | Status |
|---|---|:--:|
| `01_cardd_data_analysis.ipynb` | CarDD structure, class distribution, instances per image, dimensions | ✅ Executed |
| `02_cardd_annotation_conversion.ipynb` | CarDD COCO → YOLO segmentation conversion | 📝 Written, not yet run |
| `03_carparts_preprocessing.ipynb` | Carparts-Seg validation: splits, annotations, balance, mask quality | ✅ Executed |
| `07_cardd_baseline.ipynb` | Baseline damage model | ⬜ Placeholder |

**Completed**

- **CarDD analysed** — 4,000 images, 8,740 damage instances across the official
  train/validation/test splits.
- **Carparts-Seg validated** — 3,833 images, 23 part classes. Findings recorded,
  including 135 empty label files and an ambiguous `object` class; both remain
  open decisions.
- **Damage taxonomy agreed** — six classes, with their label mapping and
  boundary rules.
- **CarDD conversion written** — with validation checks and visual verification,
  awaiting a run against the dataset.

**Not started** — model training, damage-to-part matching, the language-model
component, the prototype interface, and system evaluation.

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
`matplotlib` · `seaborn` · `Pillow` · `PyYAML` · `jupyter`

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

Tasks are sequenced by explicit dependencies, so a task starts only once
everything it depends on is complete.

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

## Roadmap

In dependency order:

1. **Acquire the CarDD images** — required before anything can be converted or
   trained.
2. **Finalise the vehicle-part taxonomy** and resolve the open questions from
   the Carparts-Seg validation.
3. **Run and validate the CarDD conversion**, confirming the converted polygons
   align with the annotated damage.
4. **Measure the domain gap** — the part model trains on images of intact
   vehicles but must run on photographs of damaged ones.
5. **Train baseline damage and part models** and record their metrics as the
   reference for later experiments.
6. **Improve and compare** — run further experiments and select the final models
   on measured results.
7. **Build the matching, LLM and interface layers** on top of the selected
   models.

## References

- **CarDD** — Wang, Li & Wu, *CarDD: A New Dataset for Vision-Based Car Damage
  Detection*, IEEE Transactions on Intelligent Transportation Systems,
  24(7):7202–7214, 2023. [doi:10.1109/TITS.2023.3258480](https://doi.org/10.1109/TITS.2023.3258480)
  · [project site](https://cardd-ustc.github.io/)
- Further references in [`docs/references.md`](docs/references.md).

---

## Disclaimer

This project is a proof of concept and **does not replace professional vehicle
assessment**. Its output is a preliminary aid for human review, not a final
decision.
