# Qaddir: AI-Assisted Preliminary Vehicle Damage Assessment

Qaddir is a graduation project exploring AI-assisted preliminary assessment of visible vehicle damage from images.

The project aims to identify damage types, locate affected vehicle parts, and produce structured results for human review.

## Current Phase

Dataset preparation and preprocessing.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

Check the install:

```bash
python -c "import qaddir; print(qaddir.__version__)"
```

Reusable code lives in `src/qaddir/` (`data`, `cv`, `llm`, `app`). Notebooks
import from it rather than duplicating logic.

## Notebook Outputs

Notebook outputs are committed, because the project is assessed on visible
results. Before committing, restart and run all so the outputs match the code,
and never commit a notebook containing a machine-specific path or an API key.

## Data

Datasets are not included in this repository.

## Disclaimer

This project is a proof of concept and does not replace professional vehicle assessment.
