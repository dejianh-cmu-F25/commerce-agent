#!/usr/bin/env python3
"""Export real-eval failures to regression candidates (feature 043, EV-5 / RW-4).

Reads ``evals/results-real.json``, turns each failed run into a deduped candidate,
and appends new ones to ``evals/regression-candidates.jsonl``. A candidate is
**evidence, not a regression**: a human root-causes it and promotes it with
``scripts/promote_regression.py``. Idempotent (RD-2).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results-real.json"
CANDIDATES = ROOT / "evals" / "regression-candidates.jsonl"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def load_candidates(path: Path = CANDIDATES) -> list[dict]:
    if not path.exists():
        return []
    candidates: list[dict] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            candidates.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return candidates


def export(results: dict, path: Path = CANDIDATES) -> list[dict]:
    """Append new, deduped candidates; return the ones added."""
    agent = results.get("agent", {})
    records = agent.get("failure_records", [])
    existing = {(candidate["task"], candidate["category"]) for candidate in load_candidates(path)}
    seen: set[tuple[str, str]] = set()
    new: list[dict] = []
    for record in records:
        key = (record["task"], record["category"])
        if key in existing or key in seen:
            continue
        seen.add(key)
        new.append(
            {
                "task": record["task"],
                "category": record["category"],
                "seeds": [record["seed"]],
                "prompt_hash": agent.get("prompt_hash", ""),
                "status": "candidate",
            }
        )
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            for candidate in new:
                handle.write(json.dumps(candidate) + "\n")
    return new


def main() -> int:
    results = _load(RESULTS)
    if not results:
        print("no results-real.json; nothing to export (run the real eval first)")
        return 0
    new = export(results)
    print(f"exported {len(new)} new candidate(s)")
    for candidate in new:
        print(f"  {candidate['task']} ({candidate['category']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
