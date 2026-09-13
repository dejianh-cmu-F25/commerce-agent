#!/usr/bin/env python3
"""Gate for measured results (constitution P1, P7).

Verifies that the keyless numbers recorded in ``specs/RESULTS.md`` match the
freshly generated artifacts (``evals/results-keyless.json``, written by
``evals/bench.py`` and ``evals/ablation.py``). Real-model numbers are dated
snapshots and are not checked (the gate does not re-run the real model).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "evals" / "results-keyless.json"
RESULTS = ROOT / "specs" / "RESULTS.md"

RETRIEVAL_HEADING = "## Retrieval benchmark"
ABLATION_HEADING = "## Feature ablation"


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _row(section: str, config: str) -> list[str] | None:
    """Return the cells of the table row whose first cell is ``config``."""
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"| `{config}` |"):
            return [cell.strip() for cell in stripped.strip("|").split("|")]
    return None


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def main() -> int:
    if not RESULTS.exists():
        print("FAIL: specs/RESULTS.md is missing.")
        return 1

    artifacts = _load(ARTIFACTS)
    if not artifacts:
        print("SKIP: no keyless artifacts yet (run evals/bench.py and evals/ablation.py).")
        return 0

    text = RESULTS.read_text()
    failures: list[str] = []

    retrieval = artifacts.get("retrieval", {})
    if retrieval:
        section = _section(text, RETRIEVAL_HEADING)
        if not section:
            failures.append("RESULTS.md has no retrieval section")
        for config, metrics in retrieval["configs"].items():
            row = _row(section, config)
            if row is None:
                failures.append(f"retrieval row for {config!r} missing")
                continue
            expected = [
                f"{metrics['hit_rate']:.3f}",
                f"{metrics['recall']:.3f}",
                f"{metrics['mrr']:.3f}",
            ]
            actual = row[1:4]
            if actual != expected:
                failures.append(f"retrieval {config}: {actual} != {expected}")

    ablation = artifacts.get("ablation", {})
    if ablation:
        section = _section(text, ABLATION_HEADING)
        if not section:
            failures.append("RESULTS.md has no ablation section")
        for config, metrics in ablation["configs"].items():
            row = _row(section, config)
            if row is None:
                failures.append(f"ablation row for {config!r} missing")
                continue
            expected = f"{metrics['pass_rate']:.3f}"
            if row[2] != expected:
                failures.append(f"ablation {config}: pass rate {row[2]} != {expected}")

    if "## Agent reliability" not in text:
        failures.append("RESULTS.md has no real-model snapshot section")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: specs/RESULTS.md matches the keyless artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
