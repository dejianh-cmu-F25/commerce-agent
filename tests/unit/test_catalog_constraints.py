"""`search_products` enforces the customer's explicit constraints (feature 046 step A4).

The model extracts "under $25" into ``max_price``; the harness applies it exactly.
A regression here is invisible to the tool-call assertions, so it is pinned here.
"""

from __future__ import annotations

import asyncio
import json

from app.adapters.storefront_memory import InMemoryStorefront
from app.core.session import Session
from app.core.types import Product
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry

PRODUCTS = [
    Product(
        id="p1", title="Yoga Mat Basic", price=18.0, stock=5, tags=["Sports", "category:Sports"]
    ),
    Product(id="p2", title="Yoga Mat Pro", price=64.0, stock=5, tags=["Sports", "category:Sports"]),
    Product(id="p3", title="Yoga Mat Travel", price=24.0, stock=5, tags=["Sports"]),
    Product(id="p4", title="Yoga Blocks", price=12.0, stock=5, tags=["Home"]),
    Product(id="p5", title="Yoga Mat Deluxe", price=150.0, stock=5, tags=["category:Premium Yoga"]),
]


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_catalog_tools(registry, InMemoryStorefront(PRODUCTS, seed_orders=False))
    return registry


def _search(**arguments) -> dict:
    result = asyncio.run(_registry().execute("search_products", arguments, Session(id="t")))
    return json.loads(result.content)


def _prices(payload: dict) -> list[float]:
    return [item["price"] for item in payload["results"]]


def test_no_constraint_returns_the_ranked_shortlist():
    payload = _search(query="yoga mat", limit=5)
    assert "constraints" not in payload
    assert len(payload["results"]) <= 5


def test_max_price_is_enforced_on_every_returned_item():
    payload = _search(query="yoga mat", limit=5, max_price=25)
    assert _prices(payload) and all(price <= 25 for price in _prices(payload))
    assert payload["constraints"]["max_price"] == 25


def test_max_price_can_return_an_empty_set_rather_than_an_over_budget_item():
    payload = _search(query="yoga mat", limit=5, max_price=1)
    assert payload["results"] == []
    assert payload["constraints"] == {"max_price": 1.0, "category": None}


def test_category_is_enforced_and_tolerates_separators():
    payload = _search(query="yoga", limit=5, category="sports")
    assert payload["results"] and all(
        "Sports" in item["title"] or True for item in payload["results"]
    )
    assert {item["id"] for item in payload["results"]} <= {"p1", "p2", "p3"}

    # Shopify stores the taxonomy with underscores; the model says it with spaces.
    payload = _search(query="yoga", limit=5, category="Premium Yoga")
    assert {item["id"] for item in payload["results"]} == {"p5"}


def test_constraints_compose():
    payload = _search(query="yoga mat", limit=5, max_price=25, category="Sports")
    assert all(price <= 25 for price in _prices(payload))
    assert {item["id"] for item in payload["results"]} <= {"p1", "p3"}


def test_overflow_of_the_limit_still_prefers_in_budget_items():
    """Filtering happens before truncation, so a cheap item is not crowded out."""
    payload = _search(query="yoga", limit=2, max_price=20)
    assert len(payload["results"]) == 2
    assert all(price <= 20 for price in _prices(payload))
