#!/usr/bin/env python3
"""Compare two journey runs case by case (feature 046, concurrency A/B).

Concurrency must not change what is measured. This diffs two result files on the
facts that decide a score — the outcome and the tool calls — and fails when any
case disagrees.

Run::

    uv run python evals/compare_runs.py evals/results-journey-c1.json evals/results-journey.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text())
    return {case["case_id"]: case for case in data.get("per_case", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()

    left, right = _load(args.left), _load(args.right)
    only_left = sorted(set(left) - set(right))
    only_right = sorted(set(right) - set(left))
    disagreements = [
        case_id
        for case_id in sorted(set(left) & set(right))
        if left[case_id]["ok"] != right[case_id]["ok"]
        or left[case_id]["tools"] != right[case_id]["tools"]
    ]

    if not left or not right:
        print("FAIL: a run has no per_case detail (was it recorded before this change?)")
        return 1
    print(f"cases: {len(left)} vs {len(right)}")
    if only_left:
        print(f"only in {args.left.name}: {only_left[:10]}")
    if only_right:
        print(f"only in {args.right.name}: {only_right[:10]}")
    if disagreements:
        print(f"DISAGREE ({len(disagreements)}):")
        for case_id in disagreements[:20]:
            print(f"  {case_id}: {left[case_id]['ok']}/{left[case_id]['tools']}")
            print(f"  {' ' * len(case_id)}  {right[case_id]['ok']}/{right[case_id]['tools']}")
    else:
        print("identical: every case scored the same with the same tool calls")

    if only_left or only_right or disagreements:
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
