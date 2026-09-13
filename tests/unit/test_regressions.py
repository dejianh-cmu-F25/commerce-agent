"""Regression registry and runner (feature 033, RW-4/EV-5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.evaluation.regressions import load
from evals.regressions import REGISTRY, run_regressions
from scripts.promote_regression import promote


def test_registry_entries_are_complete() -> None:
    regressions = load(REGISTRY)
    assert len(regressions) >= 5
    for regression in regressions:
        assert regression.id and regression.source and regression.root_cause and regression.check


async def test_regression_runner_passes() -> None:
    result = await run_regressions()
    assert result["coverage"] == 1.0, result["failures"]


def test_promotion_requires_a_root_cause(tmp_path: Path) -> None:
    registry = tmp_path / "regressions.json"
    registry.write_text('{"regressions": []}')
    with pytest.raises(ValueError):
        promote(registry, {"id": "x", "source": "s", "root_cause": "  ", "check": "c"})


def test_promotion_is_idempotent_by_id(tmp_path: Path) -> None:
    registry = tmp_path / "regressions.json"
    registry.write_text('{"regressions": []}')
    entry = {"id": "x", "source": "s", "root_cause": "r", "check": "c"}
    assert promote(registry, entry) == "added"
    assert promote(registry, entry) == "updated"
    assert len(json.loads(registry.read_text())["regressions"]) == 1
