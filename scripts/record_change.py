#!/usr/bin/env python3
"""Append an auditable change-log entry with a computed before/after (EV-1).

Runs the keyless gold scenarios under the naked baseline and a named ablation
config, computes the pass-rate delta, and appends an entry to
``specs/change-log.json``. Refresh the rendered views afterwards:

    uv run python evals/report.py --write

Usage:
    uv run python scripts/record_change.py --change "#NN name" --config +memory
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from evals.ablation import CONFIGS
from evals.runner import RunConfig, run_scenarios

ROOT = Path(__file__).resolve().parent.parent
CHANGE_LOG = ROOT / "specs" / "change-log.json"
NAKED = RunConfig(use_memory=False, use_skills=False, knowledge="memory")


async def _pass_rate(config: RunConfig) -> float:
    results = await run_scenarios(config)
    if not results:
        return 0.0
    return round(sum(1 for item in results if item.ok) / len(results), 4)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--change", required=True, help="Change id, e.g. '#NN name'")
    parser.add_argument("--config", required=True, choices=sorted(CONFIGS))
    parser.add_argument("--metric", default="gold pass rate")
    parser.add_argument("--area", default="agent")
    parser.add_argument("--evidence", default="evals/ablation.py")
    args = parser.parse_args()

    before = asyncio.run(_pass_rate(NAKED))
    after = asyncio.run(_pass_rate(CONFIGS[args.config]))

    entry = {
        "date": datetime.now(UTC).date().isoformat(),
        "change": args.change,
        "area": args.area,
        "class": "measurable",
        "what": f"Enable {args.config}",
        "metric": args.metric,
        "before": before,
        "after": after,
        "note": f"delta {after - before:+.3f}",
        "guardrails": None,
        "verdict": "accepted",
        "evidence": args.evidence,
    }

    data: dict = {"entries": []}
    if CHANGE_LOG.exists():
        try:
            data = json.loads(CHANGE_LOG.read_text())
        except json.JSONDecodeError:
            data = {"entries": []}
    data.setdefault("entries", []).append(entry)
    CHANGE_LOG.write_text(json.dumps(data, indent=2) + "\n")

    print(f"recorded {args.change!r}: {args.metric} {before} → {after} ({after - before:+.3f})")
    print("refresh the views: uv run python evals/report.py --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
