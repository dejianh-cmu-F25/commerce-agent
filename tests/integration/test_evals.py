"""The gold scenarios pass keylessly (feature 011)."""

from __future__ import annotations

from evals.run import run_all


async def test_gold_scenarios_pass():
    results = await run_all()
    failed = [(result.name, result.failures) for result in results if not result.ok]
    assert not failed, failed
