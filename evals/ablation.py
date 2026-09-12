"""Keyless feature ablation over the gold scenarios (feature 023).

Runs the same scenarios under configurations that toggle memory, skills, and the
retrieval backend, and reports each config's pass rate and the delta vs the
naked baseline — the "I changed X → effect Y" evidence. Keyless and
deterministic; runs in the gate.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from evals.runner import RunConfig, run_scenarios

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"

CONFIGS: dict[str, RunConfig] = {
    "naked": RunConfig(use_memory=False, use_skills=False, knowledge="memory"),
    "+memory": RunConfig(use_memory=True, use_skills=False, knowledge="memory"),
    "+skills": RunConfig(use_memory=False, use_skills=True, knowledge="memory"),
    "+dense-hash": RunConfig(use_memory=False, use_skills=False, knowledge="dense-hash"),
    "+dense-chroma": RunConfig(use_memory=False, use_skills=False, knowledge="dense-chroma"),
}


async def run_ablation() -> dict:
    result: dict = {"configs": {}}
    for name, config in CONFIGS.items():
        results = await run_scenarios(config)
        passed = sum(1 for item in results if item.ok)
        result["configs"][name] = {
            "passed": passed,
            "total": len(results),
            "pass_rate": round(passed / len(results), 4) if results else 0.0,
            "failed": [item.name for item in results if not item.ok],
        }
    return result


def write_keyless(ablation: dict) -> None:
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["ablation"] = ablation
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    result = asyncio.run(run_ablation())
    baseline = result["configs"]["naked"]["pass_rate"]
    print("feature ablation (keyless gold scenarios)")
    for name, metrics in result["configs"].items():
        delta = metrics["pass_rate"] - baseline
        print(
            f"  {name:<14} {metrics['passed']}/{metrics['total']} "
            f"({metrics['pass_rate']:.3f})  delta {delta:+.3f}"
        )
    write_keyless(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
