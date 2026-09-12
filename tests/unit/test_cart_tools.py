"""Unit tests for the cart tools (feature 009)."""

from __future__ import annotations

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.storefront_memory import InMemoryStorefront
from app.core.session import Session
from app.tools.cart import register_cart_tools
from app.tools.registry import ToolRegistry


def make() -> ToolRegistry:
    registry = ToolRegistry()
    register_cart_tools(registry, InMemoryStorefront(SEED_PRODUCTS))
    return registry


async def test_add_rejects_ungrounded_id():
    session = Session(id="s1")
    result = await make().execute("add_to_cart", {"product_id": "P-101"}, session)
    assert result.status == "error"
    assert session.cart == []


async def test_add_grounded_product_then_increment():
    registry = make()
    session = Session(id="s1")
    session.remember_ids(["P-101"])

    first = await registry.execute("add_to_cart", {"product_id": "P-101", "quantity": 2}, session)
    assert first.status == "ok"
    assert first.component == "cart"
    assert first.payload is not None
    assert first.payload["total"] == 378.0
    assert session.cart[0].quantity == 2

    await registry.execute("add_to_cart", {"product_id": "P-101"}, session)
    assert len(session.cart) == 1  # no duplicate line (RD-2)
    assert session.cart[0].quantity == 3


async def test_quantity_is_clamped_to_one():
    session = Session(id="s1")
    session.remember_ids(["P-101"])
    await make().execute("add_to_cart", {"product_id": "P-101", "quantity": 0}, session)
    assert session.cart[0].quantity == 1


async def test_checkout_renders_and_never_charges():
    registry = make()
    session = Session(id="s1")
    session.remember_ids(["P-101"])
    await registry.execute("add_to_cart", {"product_id": "P-101"}, session)

    result = await registry.execute("render_checkout", {}, session)
    assert result.component == "checkout"
    assert result.payload is not None
    assert result.payload["charged"] is False
    assert result.payload["total"] == 189.0


async def test_view_cart_returns_current_lines():
    registry = make()
    session = Session(id="s1")
    session.remember_ids(["P-104"])
    await registry.execute("add_to_cart", {"product_id": "P-104"}, session)

    result = await registry.execute("view_cart", {}, session)
    assert result.component == "cart"
    assert result.payload is not None
    assert result.payload["items"][0]["product_id"] == "P-104"
