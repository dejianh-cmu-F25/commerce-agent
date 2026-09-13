"""Run the gold scenarios keylessly and report pass/fail (P7, TT-2).

A thin CLI over :func:`evals.runner.run_scenarios`, which the web Scenario Runner
also uses (feature 016), so the gate and the browser cannot drift. It also writes
the intent/tool segments to the keyless artifact (feature 030, SC-2).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.evaluation.segments import by_intent, by_tool
from evals.runner import ScenarioResult, run_scenarios

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"

# Backwards-compatible alias for callers that import the old name.
run_all = run_scenarios


def write_segments(results: list[ScenarioResult]) -> dict:
    segments = {"by_intent": by_intent(results), "by_tool": by_tool(results)}
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["segments"] = segments
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    return segments


def main() -> int:
    results = asyncio.run(run_scenarios())
    width = max((len(result.name) for result in results), default=0)
    for result in results:
        print(f"{result.name:<{width}}  {'PASS' if result.ok else 'FAIL'}")
        for failure in result.failures:
            print(f"    - {failure}")
    failed = [result for result in results if not result.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} scenarios passed")

    segments = write_segments(results)
    print("\nby intent:")
    for intent, metrics in segments["by_intent"].items():
        print(f"  {intent:<10} {metrics['passed']:.0f}/{metrics['total']:.0f}")
    print("by tool:")
    for tool, metrics in segments["by_tool"].items():
        print(f"  {tool:<22} calls={metrics['calls']:.0f} errors={metrics['errors']:.0f}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
