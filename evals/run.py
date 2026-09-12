"""Run the gold scenarios keylessly and report pass/fail (P7, TT-2).

A thin CLI over :func:`evals.runner.run_scenarios`, which the web Scenario Runner
also uses (feature 016), so the gate and the browser cannot drift.
"""

from __future__ import annotations

import asyncio

from evals.runner import run_scenarios

# Backwards-compatible alias for callers that import the old name.
run_all = run_scenarios


def main() -> int:
    results = asyncio.run(run_scenarios())
    width = max((len(result.name) for result in results), default=0)
    for result in results:
        print(f"{result.name:<{width}}  {'PASS' if result.ok else 'FAIL'}")
        for failure in result.failures:
            print(f"    - {failure}")
    failed = [result for result in results if not result.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
