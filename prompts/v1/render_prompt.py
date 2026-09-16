#!/usr/bin/env python3
"""Render Prompt V1 for one fixture.

Substitutes the TEST-ONLY threshold values from test_thresholds.json into the
placeholder tokens in prompt_v1.md, then appends the user message for the given
fixture. Rendering is the only point at which numeric threshold values enter the
prompt; see test_thresholds.json for why they are not production policy.

Usage:  python3 render_prompt.py fixtures/f01_high_confidence_single.json
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent


def render(fixture_path: Path) -> str:
    cfg = json.loads((HERE / "test_thresholds.json").read_text())["thresholds"]
    prompt = (HERE / "prompt_v1.md").read_text()

    # the system prompt is the first fenced block under "## 1. System Prompt"
    body = prompt.split("## 1. System Prompt", 1)[1]
    system = body.split("```text", 1)[1].split("```", 1)[0].strip()

    for name, value in cfg.items():
        system = system.replace("{{%s}}" % name, str(value))

    unresolved = re.findall(r"\{\{(\w+)\}\}", system)
    if unresolved:
        raise SystemExit("unresolved placeholders: %s" % unresolved)

    cv_json = (HERE / fixture_path).read_text().strip() if not Path(fixture_path).is_absolute() \
        else Path(fixture_path).read_text().strip()

    user = (
        "Generate a preliminary damage report from the following structured "
        "detection output. Use only the fields present.\n\n" + cv_json
    )
    return system + "\n\n---\n\n" + user


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(render(Path(sys.argv[1])))
