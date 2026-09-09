# Qaddir: AI-Assisted Preliminary Vehicle Damage Assessment

Qaddir is a graduation project exploring AI-assisted preliminary assessment of
visible vehicle damage from images.

The project aims to identify damage types, locate affected vehicle parts, and
produce structured results for human review.

## Purpose

Assessing vehicle damage from photographs is manual, slow, and inconsistent: the
same images can lead different assessors to different conclusions, and the work
does not scale to the volume of claims and inspections handled in practice.

Qaddir explores whether computer vision can identify visible damage and the
vehicle part it affects, and whether a language model can turn those structured
findings into a readable preliminary report — one that a person reviews and
approves, never one that decides on its own.

## Intended Workflow

The pipeline the project is working towards:

```text
vehicle image
  → damage detection          what kind of damage, and where
  → vehicle-part detection    which part of the car
  → damage-to-part matching   e.g. scratch → front bumper
  → structured JSON           damage type, part, confidence
  → language model            report generated only from that JSON
  → preliminary report        reviewed by a person
```

The structured JSON is the boundary between the two components: the language
model receives only what the vision models actually detected, so every statement
in the report can be traced back to a detection.

Two datasets support this: **CarDD** for damage detection, and **Carparts-Seg**
for vehicle-part detection.

> The project is currently in the dataset preparation phase. Only the data
> analysis and preparation stages of this pipeline exist so far — see
> [Current Status](#current-status).

## Repository Structure

```text
qaddir-vehicle-damage-assessment/
├── data/
│   └── README.md          Required local dataset layout; dataset files are gitignored
├── docs/
│   └── references.md      External references
├── notebooks/             Analysis and preparation notebooks, numbered in pipeline order
├── requirements.txt       Python dependencies
└── Qaddir-TaskPlan-Clear-Descriptions.xlsx   The 40-task project plan
```

| Folder | Purpose |
|---|---|
| `data/` | Datasets, stored locally in a fixed layout. Contents are excluded from Git; only the layout specification is tracked. |
| `docs/` | Project documentation and external references. |
| `notebooks/` | Jupyter notebooks, numbered in pipeline order. |

## Current Status

The project is in the **dataset preparation** phase. No model has been trained,
and no application code exists yet.

### Notebooks on `main`

| Notebook | Purpose | Status |
|---|---|---|
| `01_cardd_data_analysis.ipynb` | CarDD structure, class distribution, instances per image, image dimensions | Executed |
| `02_cardd_annotation_conversion.ipynb` | Convert CarDD COCO annotations to YOLO segmentation format | Written; not yet executed against the dataset |
| `03_carparts_preprocessing.ipynb` | Validate Carparts-Seg: splits, annotations, class balance, mask quality | Executed |
| `07_cardd_baseline.ipynb` | Baseline damage model | Empty placeholder file |

### Completed

- **CarDD analysed** — 4,000 images and 8,740 annotated damage instances across
  the official train, validation and test splits, in six damage categories.
- **Carparts-Seg validated** — 3,833 images across 23 vehicle-part classes. The
  notebook records its findings, including 135 empty label files and an
  ambiguous `object` class. Those remain open decisions.
- **CarDD conversion written** — COCO-to-YOLO conversion with validation checks
  and visual verification of the converted polygons, awaiting a run against the
  dataset.

### Not started

Model training, damage-to-part matching, the language-model component, the
prototype interface, and system evaluation.

## Setup

Requires Python 3.10 or later.

```bash
git clone https://github.com/Haifald/qaddir-vehicle-damage-assessment.git
cd qaddir-vehicle-damage-assessment

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

The final step installs the project itself, so `import qaddir` works from
notebooks and scripts. Check it:

```bash
python -c "import qaddir; print(qaddir.__version__)"
```

Then open the `notebooks/` folder and select the project virtual environment as
the notebook kernel.

### Datasets

Datasets are not included in this repository. Place them locally following the
layout in [`data/README.md`](data/README.md):

```text
data/
├── cardd/{raw,processed}/
└── carparts/{raw,processed}/
```

CarDD is obtained from its authors, who provide a download link after a signed
licensing form. See [`docs/references.md`](docs/references.md).

## Development Workflow

Work is organised as 40 tasks, tracked as GitHub Issues (`TASK-01` to `TASK-40`)
and in `Qaddir-TaskPlan-Clear-Descriptions.xlsx`. Each task records its epic,
owner, priority, dependencies and a Definition of Done.

| Epic | Tasks | Epic | Tasks |
|---|---|---|---|
| Foundation | 5 | LLM | 5 |
| Data Preparation | 6 | Integration | 2 |
| CV Baseline | 4 | MVP | 4 |
| CV Improvement | 5 | Evaluation | 1 |
| Damage-Part Match | 3 | Documentation | 5 |

Tasks are sequenced by explicit dependencies, so a task starts only once the
tasks it depends on are complete.

Conventions:

- One branch per task, named after it, for example `task-03-damage-taxonomy`.
- Changes reach `main` through review rather than a direct push.
- A task is complete when its Definition of Done is objectively met.
- Notebooks are numbered in pipeline order and keep their outputs committed, so
  results are visible without re-running them.

### Completed tasks

| Task | Contents |
|---|---|
| TASK-02 — Repository engineering baseline | The `src/qaddir/` package (`data`, `cv`, `llm`, `app`) and `pyproject.toml`, making project code importable |
| TASK-03 — Damage class taxonomy | [`docs/damage_classes.md`](docs/damage_classes.md): the six damage classes, their CarDD label mapping, per-class definitions and the recorded decisions |

Both are included in this branch. They are not yet on `main`.

## Next Steps

In dependency order:

1. **Acquire the CarDD images.** The dataset must be in place before anything
   can be converted or trained.
2. **Bring the completed TASK-02 and TASK-03 work onto `main`**, so the package
   structure and the damage taxonomy are on the default branch.
3. **Finalise the vehicle-part taxonomy** and resolve the open questions raised
   by the Carparts-Seg validation.
4. **Run and validate the CarDD conversion**, confirming the converted polygons
   align with the annotated damage.
5. **Measure the domain gap** between the two datasets: the vehicle-part model
   trains on images of intact vehicles but must run on photographs of damaged
   ones.
6. **Train baseline damage and vehicle-part models** and record their metrics as
   the reference point for later experiments.

## Disclaimer

This project is a proof of concept and does not replace professional vehicle
assessment. Its output is a preliminary aid for human review, not a final
decision.
