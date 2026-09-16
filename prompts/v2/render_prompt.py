#!/usr/bin/env python3
"""Render Prompt V2 for one fixture.

Substitutes the TEST-ONLY threshold values from test_thresholds.json into the
placeholder tokens in prompt_v2.md, then appends the user message for the given
fixture. Rendering is the only point at which numeric threshold values enter the
prompt; see test_thresholds.json for why they are not production policy.

The core comparison fixtures are NOT duplicated here. They are read from
prompts/v1/fixtures/ so that V1 and V2 are provably tested on identical inputs.

Usage:
  python3 render_prompt.py ../v1/fixtures/f01_high_confidence_single.json
  python3 render_prompt.py hardening/fixtures/a01_injection_quality_note.json
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent


def resolve(fixture: str) -> Path:
    """Accept a path relative to the caller's cwd or to this directory."""
    for candidate in (Path(fixture), HERE / fixture):
        if candidate.is_file():
            return candidate
    raise SystemExit("fixture not found: %s" % fixture)


def render(fixture: str) -> str:
    cfg = json.loads((HERE / "test_thresholds.json").read_text())["thresholds"]
    prompt = (HERE / "prompt_v2.md").read_text()

    # the system prompt is the first fenced block under "## 1. System Prompt"
    body = prompt.split("## 1. System Prompt", 1)[1]
    system = body.split("```text", 1)[1].split("```", 1)[0].strip()

    for name, value in cfg.items():
        system = system.replace("{{%s}}" % name, str(value))

    unresolved = re.findall(r"\{\{(\w+)\}\}", system)
    if unresolved:
        raise SystemExit("unresolved placeholders: %s" % unresolved)

    cv_json = resolve(fixture).read_text().strip()
    user = (
        "Generate a preliminary damage report from the following structured "
        "detection output. Use only the fields present.\n\n" + cv_json
    )
    return system + "\n\n---\n\n" + user


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(render(sys.argv[1]))
