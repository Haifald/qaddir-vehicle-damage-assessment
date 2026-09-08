# Qaddir: AI-Assisted Preliminary Vehicle Damage Assessment

Qaddir is a graduation project exploring AI-assisted preliminary assessment of visible vehicle damage from images.

The project aims to identify damage types, locate affected vehicle parts, and produce structured results for human review.

## Current Phase

Dataset preparation and preprocessing.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

Check the install:

```bash
python -c "import qaddir; print(qaddir.paths.describe())"
```

Then open `notebooks/` and select the project virtual environment as the kernel.

## Repository Layout

| Path | Contents |
|---|---|
| `notebooks/` | Analysis and reporting notebooks, numbered in pipeline order |
| `src/qaddir/` | Reusable code: `data`, `cv`, `llm`, `app` |
| `configs/` | Training and experiment configurations |
| `docs/` | Dataset, model and design documentation |
| `data/` | Datasets, excluded from Git. See `data/README.md` |

## Data

Datasets are not included in this repository. Place them locally following
`data/README.md`, then reference them through `qaddir.paths`.

## Contributing

See `CONTRIBUTING.md` for setup, notebook conventions and the branch workflow.

## Disclaimer

This project is a proof of concept and does not replace professional vehicle assessment.
