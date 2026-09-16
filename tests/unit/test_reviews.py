"""Real review store and the get_reviews tool (feature 046)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.adapters.reviews_sqlite import SqliteReviewStore
from app.core.session import Session
from app.core.types import Product
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


class FakeCatalog:
    """A catalog whose products carry the source ASIN as their SKU."""

    def __init__(self, products: list[Product]) -> None:
        self._products = {p.id: p for p in products}

    def get(self, product_id: str) -> Product | None:
        return self._products.get(product_id)


def test_a_shopify_id_is_resolved_to_the_review_key(tmp_path: Path) -> None:
    """Reviews are keyed by ASIN; search returns a gid. The tool bridges them.

    Regression: without the bridge `get_reviews` returned nothing for every product
    the agent could actually see, because the ids never matched.
    """
    catalog = FakeCatalog(
        [Product(id="gid://shopify/Product/1", title="Tent", price=10.0, stock=1, sku="B1")]
    )
    registry = ToolRegistry()
    register_review_tools(registry, _store(tmp_path), catalog)
    result = asyncio.run(
        registry.execute("get_reviews", {"product_id": "gid://shopify/Product/1"}, Session(id="t"))
    )
    payload = json.loads(result.content)
    assert [r["title"] for r in payload["reviews"]] == ["Great", "Okay"]


def test_an_unresolvable_id_falls_back_to_itself(tmp_path: Path) -> None:
    """Keyless fixtures and ASIN-keyed callers keep working unchanged."""
    registry = ToolRegistry()
    register_review_tools(registry, _store(tmp_path), FakeCatalog([]))
    result = asyncio.run(registry.execute("get_reviews", {"product_id": "B2"}, Session(id="t")))
    assert json.loads(result.content)["reviews"][0]["title"] == "Good"


def test_a_product_without_a_sku_uses_its_own_id(tmp_path: Path) -> None:
    catalog = FakeCatalog(
        [Product(id="B2", title="Tent", price=10.0, stock=1)]  # no sku (fixture product)
    )
    registry = ToolRegistry()
    register_review_tools(registry, _store(tmp_path), catalog)
    result = asyncio.run(registry.execute("get_reviews", {"product_id": "B2"}, Session(id="t")))
    assert json.loads(result.content)["reviews"][0]["title"] == "Good"
