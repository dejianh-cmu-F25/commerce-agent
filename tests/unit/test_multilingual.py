"""Multilingual retrieval is measured per language (feature 040, RW-1)."""

from __future__ import annotations

from evals.bench import run_multilingual


def test_multilingual_measured_per_language() -> None:
    result = run_multilingual()
    assert result["gated"] is False
    assert result["cases"] >= 8
    assert {"es", "fr", "de", "zh"} <= set(result["by_language"])
    assert all(0.0 <= rate <= 1.0 for rate in result["by_language"].values())
