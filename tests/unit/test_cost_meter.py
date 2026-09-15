"""Cost meter: throttled persistence and concurrency headroom (feature 046)."""

from __future__ import annotations

import json

from app.adapters.cost_meter import PERSIST_EVERY_CNY, UsageCostMeter
from app.core.settings import BudgetSettings
from app.core.types import Usage


def _settings(tmp_path, **overrides) -> BudgetSettings:
    defaults = {"state_file": str(tmp_path / "budget.json")}
    return BudgetSettings(**{**defaults, **overrides})


def _usage(prompt: int = 1_000, completion: int = 0) -> Usage:
    return Usage(prompt_tokens=prompt, completion_tokens=completion)


def test_throttles_persistence_but_keeps_the_running_total(tmp_path):
    meter = UsageCostMeter(_settings(tmp_path))
    meter.record(_usage())
    # One call is below the persist threshold: the file is not written yet...
    assert not (tmp_path / "budget.json").exists()
    # ...but the in-memory total is accurate.
    assert meter.spent_cny() > 0
    meter.flush()
    assert json.loads((tmp_path / "budget.json").read_text())["spent_cny"] == round(
        meter.spent_cny(), 6
    )


def test_persists_once_the_interval_is_crossed(tmp_path):
    settings = _settings(tmp_path)
    meter = UsageCostMeter(settings)
    per_call = meter.cost_of(_usage())
    calls = int(PERSIST_EVERY_CNY / per_call) + 1
    for _ in range(calls):
        meter.record(_usage())
    assert (tmp_path / "budget.json").exists()


def test_reload_resumes_the_saved_total(tmp_path):
    settings = _settings(tmp_path)
    first = UsageCostMeter(settings)
    first.record(_usage())
    first.flush()
    second = UsageCostMeter(settings)
    assert second.spent_cny() == first.spent_cny()


def test_headroom_makes_over_budget_conservative(tmp_path):
    meter = UsageCostMeter(_settings(tmp_path, total_limit=1.0))
    assert not meter.over_budget()
    meter.set_headroom(1.5)
    assert meter.over_budget()
    meter.set_headroom(0.0)
    assert not meter.over_budget()


def test_disabled_budget_never_overspends_the_guard(tmp_path):
    meter = UsageCostMeter(_settings(tmp_path, enabled=False, total_limit=0.0))
    meter.record(_usage())
    assert not meter.over_budget()
