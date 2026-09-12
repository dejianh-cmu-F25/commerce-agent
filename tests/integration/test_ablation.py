"""Integration tests for the feature ablation (feature 023)."""

from __future__ import annotations

from evals.ablation import CONFIGS, run_ablation


async def test_ablation_reports_feature_contributions():
    result = await run_ablation()
    configs = result["configs"]

    assert set(configs) == set(CONFIGS)
    baseline = configs["naked"]["pass_rate"]
    assert configs["+memory"]["pass_rate"] > baseline
    assert configs["+skills"]["pass_rate"] > baseline
