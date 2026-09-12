"""Unit tests for the spend guard (constitution HR-12)."""

from __future__ import annotations

from app.adapters.cost_meter import NullCostMeter, UsageCostMeter
from app.core.settings import BudgetSettings
from app.core.types import Usage


def make_meter(tmp_path, **overrides) -> UsageCostMeter:
    settings = BudgetSettings(
        total_limit=10.0,
        usd_to_cny=7.25,
        input_cache_miss_per_1m=0.30,
        input_cache_hit_per_1m=0.006,
        output_per_1m=1.20,
        state_file=str(tmp_path / "budget.json"),
        **overrides,
    )
    return UsageCostMeter(settings)


def test_cost_of_matches_configured_prices(tmp_path):
    meter = make_meter(tmp_path)
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, cache_miss_tokens=1_000_000)
    # (0.30 input + 1.20 output) USD * 7.25 = 10.875 CNY
    assert abs(meter.cost_of(usage) - 10.875) < 1e-6


def test_cache_hit_tokens_are_cheaper(tmp_path):
    meter = make_meter(tmp_path)
    miss = Usage(prompt_tokens=1_000_000, cache_miss_tokens=1_000_000)
    hit = Usage(prompt_tokens=1_000_000, cache_hit_tokens=1_000_000)
    assert meter.cost_of(hit) < meter.cost_of(miss)


def test_total_persists_and_blocks(tmp_path):
    meter = make_meter(tmp_path)
    meter.record(
        Usage(prompt_tokens=1_000_000, cache_miss_tokens=1_000_000, completion_tokens=1_000_000)
    )
    assert meter.spent_cny() > 10.0
    assert meter.over_budget() is True

    reopened = UsageCostMeter(meter._settings)  # noqa: SLF001 - verify persistence
    assert abs(reopened.spent_cny() - meter.spent_cny()) < 1e-9


def test_null_meter_never_blocks():
    meter = NullCostMeter()
    assert meter.over_budget() is False
    meter.record(Usage(prompt_tokens=10**9, completion_tokens=10**9))
    assert meter.spent_cny() == 0.0
