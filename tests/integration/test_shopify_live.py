"""Opt-in live Shopify integration test (feature 045).

Skipped unless SHOPIFY_SHOP and SHOPIFY_ACCESS_TOKEN are set in the environment
(they are not loaded from .env by the gate, so the default run stays keyless).
Read-only: it makes no writes against the store.
"""

from __future__ import annotations

import os

import pytest

from app.adapters.shopify_client import ShopifyAdminClient
from app.adapters.shopify_post_purchase import ShopifyPostPurchase

pytestmark = pytest.mark.skipif(
    not (os.environ.get("SHOPIFY_SHOP") and os.environ.get("SHOPIFY_ACCESS_TOKEN")),
    reason="SHOPIFY_SHOP / SHOPIFY_ACCESS_TOKEN not set; live test skipped",
)


def _client() -> ShopifyAdminClient:
    return ShopifyAdminClient(
        os.environ["SHOPIFY_SHOP"],
        os.environ["SHOPIFY_ACCESS_TOKEN"],
        os.environ.get("SHOPIFY_API_VERSION", "2025-07"),
    )


async def test_live_shop_query_authenticates() -> None:
    admin = _client()
    data = await admin.query("{ shop { name myshopifyDomain } }")
    assert data["shop"]["myshopifyDomain"]
    assert admin.last_cost is not None  # GraphQL cost is captured


async def test_live_order_and_returnable_items() -> None:
    admin = _client()
    backend = ShopifyPostPurchase(admin)
    data = await admin.query("{ orders(first: 1) { edges { node { id } } } }")
    edges = data["orders"]["edges"]
    if not edges:
        pytest.skip("no orders in the dev store yet")
    order_id = edges[0]["node"]["id"]
    order = await backend.get_order(order_id)
    assert order is not None and order.name
    assert order.currency  # a real MoneyBag was mapped
    items = await backend.returnable_items(order_id)
    assert isinstance(items, list)  # empty when the order is not fulfilled
