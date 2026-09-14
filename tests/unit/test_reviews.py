"""Real review store and the get_reviews tool (feature 046)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.adapters.reviews_sqlite import SqliteReviewStore
from app.core.session import Session
from app.ports.reviews import Review
from app.tools.registry import ToolRegistry
from app.tools.reviews import register_review_tools


def _store(tmp_path: Path) -> SqliteReviewStore:
    store = SqliteReviewStore(tmp_path / "reviews.sqlite")
    store.add(
        [
            Review("B1", 5.0, "Great", "Loved it", helpful_votes=10, verified=True, timestamp_ms=2),
            Review("B1", 3.0, "Okay", "It's fine", helpful_votes=1, timestamp_ms=3),
            Review("B2", 4.0, "Good", "Solid", helpful_votes=5, timestamp_ms=4),
        ]
    )
    return store


def test_store_returns_most_helpful_first(tmp_path: Path) -> None:
    store = _store(tmp_path)
    reviews = store.get_reviews("B1", 5)
    assert [r.rating for r in reviews] == [5.0, 3.0]
    assert reviews[0].verified is True


def test_store_unknown_product(tmp_path: Path) -> None:
    assert _store(tmp_path).get_reviews("nope") == []


def test_get_reviews_tool(tmp_path: Path) -> None:
    registry = ToolRegistry()
    register_review_tools(registry, _store(tmp_path))
    result = asyncio.run(registry.execute("get_reviews", {"product_id": "B2"}, Session(id="t")))
    payload = json.loads(result.content)
    assert payload["reviews"][0]["title"] == "Good"
    assert result.component == "reviews"
