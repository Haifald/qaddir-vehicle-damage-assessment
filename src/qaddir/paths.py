"""Canonical project paths.

Import these instead of hard-coding relative paths such as ``../data``. A
notebook run from ``notebooks/`` and a script run from the repository root then
resolve to the same location.

    from qaddir.paths import CARDD_RAW
    print(CARDD_RAW)
"""

from pathlib import Path

# This file is src/qaddir/paths.py, so the repository root is three levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
CONFIGS_DIR = PROJECT_ROOT / "configs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Datasets. Contents are gitignored: see data/README.md.
CARDD_RAW = DATA_DIR / "cardd" / "raw"
CARDD_PROCESSED = DATA_DIR / "cardd" / "processed"
CARPARTS_RAW = DATA_DIR / "carparts" / "raw"
CARPARTS_PROCESSED = DATA_DIR / "carparts" / "processed"

# Generated artefacts, also gitignored.
MODELS_DIR = PROJECT_ROOT / "models"
RUNS_DIR = PROJECT_ROOT / "runs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def describe() -> str:
    """Return each path and whether it currently exists, for quick diagnostics."""
    entries = {
        name: value
        for name, value in globals().items()
        if isinstance(value, Path) and name.isupper()
    }
    width = max(len(name) for name in entries)
    lines = [
        f"{name:<{width}}  {'exists' if path.exists() else 'missing':>7}  {path}"
        for name, path in sorted(entries.items())
    ]
    return "\n".join(lines)
