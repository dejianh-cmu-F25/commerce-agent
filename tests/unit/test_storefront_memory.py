"""Unit tests for the in-memory storefront provider (feature 004)."""

from __future__ import annotations

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.storefront_memory import InMemoryStorefront


def make() -> InMemoryStorefront:
    return InMemoryStorefront(SEED_PRODUCTS)


def test_search_matches_title_and_tags():
    results = make().search("tent", 5)
    assert [p.id for p in results] == ["P-101"]


def test_search_ranks_by_overlap_then_price():
    results = make().search("camping", 5)
    # Every seed product is tagged "camping"; ties break by lower price.
    prices = [p.price for p in results]
    assert prices == sorted(prices)


def test_search_empty_query_returns_nothing():
    assert make().search("   ", 5) == []


def test_search_respects_limit_and_clamps():
    store = make()
    assert len(store.search("camping", 2)) == 2
    # limit is clamped to at least 1
    assert len(store.search("camping", 0)) == 1


def test_get_returns_product_or_none():
    store = make()
    assert store.get("P-101") is not None
    assert store.get("nope") is None
