"""Qaddir - AI-assisted preliminary vehicle damage assessment.

Reusable project code lives here so that notebooks, tests and the Streamlit
application all share one implementation. Notebooks explore and report;
anything a second caller needs belongs in this package.

Subpackages
-----------
data : dataset conversion, cleaning and validation
cv   : model training, inference and evaluation
llm  : prompt construction, LLM calls and report generation
app  : the Streamlit MVP
"""

__version__ = "0.1.0"

from qaddir import paths

__all__ = ["paths", "__version__"]
