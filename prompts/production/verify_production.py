#!/usr/bin/env python3
"""Verify the frozen production prompt is byte-identical to what TASK-27 scored.

Fails if the frozen copy has drifted from its evaluated source, or if either has
been edited since freezing. A failure means the TASK-27 scores no longer describe
the prompt in production.

Usage:  python3 verify_production.py
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = os.path.dirname(HERE)


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    manifest = os.path.join(HERE, "MANIFEST.sha256")
    recorded = {}
    for line in open(manifest):
        m = re.match(r"^([0-9a-f]{64})\s+(\S+)\s+\((.+)\)$", line.strip())
        if m:
            recorded[m.group(2)] = (m.group(1), m.group(3))

    failures = []
    for rel, (want, label) in sorted(recorded.items()):
        path = os.path.join(PROMPTS, rel)
        if not os.path.exists(path):
            failures.append("MISSING  %s" % rel)
            continue
        got = sha256(path)
        status = "ok" if got == want else "CHANGED"
        if got != want:
            failures.append("CHANGED  %s (%s)" % (rel, label))
        print("%-8s %-42s %s" % (status, rel, got[:16] + "..."))

    pairs = [("v2/prompt_v2.md", "production/prompt_production.md"),
             ("v2/test_thresholds.json", "production/evaluation_thresholds.json")]
    print()
    for src, frozen in pairs:
        a, b = os.path.join(PROMPTS, src), os.path.join(PROMPTS, frozen)
        if os.path.exists(a) and os.path.exists(b):
            same = sha256(a) == sha256(b)
            print("%-8s %s == %s" % ("ok" if same else "DRIFT", src, frozen))
            if not same:
                failures.append("DRIFT between %s and %s" % (src, frozen))

    print()
    if failures:
        print("FAILED — the production prompt no longer matches what TASK-27 scored:")
        for f in failures:
            print("   ", f)
        print("\nRe-evaluate as a new version rather than editing the frozen prompt.")
        return 1
    print("PASSED — production prompt is byte-identical to the evaluated Prompt V2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
