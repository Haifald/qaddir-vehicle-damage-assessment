# Contributing

Conventions for the Qaddir project. They exist so that any team member can run
the project, and so that what we demonstrate is what we measured.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                   # makes `import qaddir` work
```

Verify:

```bash
python -c "import qaddir; print(qaddir.__version__); print(qaddir.paths.describe())"
```

## Repository layout

| Path | Contents |
|---|---|
| `notebooks/` | Exploration, analysis and reporting |
| `src/qaddir/` | Reusable code: `data`, `cv`, `llm`, `app` |
| `configs/` | Training and experiment configurations |
| `docs/` | Dataset, model, experiment and design documentation |
| `data/` | Datasets. Gitignored: see `data/README.md` |
| `models/`, `runs/`, `outputs/` | Generated artefacts. Gitignored |

## Notebooks

**Naming:** `NN_topic.ipynb`, two digits, lowercase, underscores.
Numbering follows the pipeline order, so the sequence reads as the project does.

**Outputs are committed.** The capstone is assessed on visible results, and a
notebook with stripped outputs cannot be graded without re-running it. The cost
is noisy diffs, which we accept.

Because outputs are committed:

- Never commit a notebook containing a machine-specific path, an API key or
  personal data. Use `qaddir.paths` rather than `../data/...` or `C:\Users\...`.
- Restart and run all before committing, so the outputs match the code.
- Do not commit a notebook whose cells were run out of order.

**Notebooks call the package; the package never imports a notebook.** Once a
second caller needs a piece of logic, move it into `src/qaddir/` and import it
back into the notebook.

## Paths

Import paths, never hard-code them:

```python
from qaddir.paths import CARDD_RAW, CARDD_PROCESSED
```

This keeps a notebook run from `notebooks/` and a script run from the repository
root pointing at the same place, on any machine and any operating system.

## Secrets

API keys go in `.env`, which is gitignored. Copy `.env.example` and fill it in.
Never commit a key or paste one into a notebook cell.

## Branches and pull requests

- Branch per task, named after its issue: `task-02-repo-engineering-baseline`.
- Reference the issue in the pull request so it closes on merge.
- No direct pushes to `main`.
- A reviewer other than the author confirms the task's Definition of Done.

## Definition of Done

Every task's Definition of Done lives in its GitHub issue and in
`Qaddir-TaskPlan-Clear-Descriptions.xlsx`. A task is Done when those criteria
are objectively met, not when the code appears to work.
