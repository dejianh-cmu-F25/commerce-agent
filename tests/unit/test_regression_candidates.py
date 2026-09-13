"""Real-eval failures export to deduped candidates (feature 043, EV-5)."""

from __future__ import annotations

from pathlib import Path

from scripts.export_regression_candidates import export, load_candidates


def _results() -> dict:
    return {
        "agent": {
            "prompt_hash": "abc123",
            "failure_records": [
                {"task": "multi_item_cart", "seed": 0, "category": "incomplete"},
                {"task": "multi_item_cart", "seed": 1, "category": "incomplete"},
                {"task": "order_status", "seed": 0, "category": "ungrounded"},
            ],
        }
    }


def test_export_dedupes_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "candidates.jsonl"
    new = export(_results(), path)
    assert len(new) == 2  # two distinct (task, category) pairs
    assert export(_results(), path) == []  # re-export adds nothing
    candidates = load_candidates(path)
    assert len(candidates) == 2
    assert all(candidate["status"] == "candidate" for candidate in candidates)


def test_export_noop_without_records(tmp_path: Path) -> None:
    path = tmp_path / "candidates.jsonl"
    assert export({"agent": {}}, path) == []
    assert not path.exists()
