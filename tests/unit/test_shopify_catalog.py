"""Shopify catalog adapter maps the Admin API to Product (feature 046)."""

from __future__ import annotations

import httpx

from app.adapters.shopify_catalog import ShopifyCatalog

_PAYLOAD = {
    "data": {
        "products": {
            "nodes": [
                {
                    "id": "gid://shopify/Product/1",
                    "title": "Trail Tent",
                    "tags": ["camping", "imported:reviews23"],
                    "variants": {"nodes": [{"price": "189.00", "inventoryQuantity": 12}]},
                }
            ]
        }
    }
}


def _catalog(handler: object) -> ShopifyCatalog:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return ShopifyCatalog("shop.myshopify.com", "tok", client=httpx.Client(transport=transport))


def test_search_maps_products() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_PAYLOAD)

    products = _catalog(handler).search("tent", 5)
    assert len(products) == 1
    assert products[0].id == "gid://shopify/Product/1"
    assert products[0].title == "Trail Tent"
    assert products[0].price == 189.0
    assert products[0].stock == 12
    assert "camping" in products[0].tags


def test_empty_query_returns_nothing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - not called
        raise AssertionError("no request expected for an empty query")

    assert _catalog(handler).search("   ", 5) == []


def test_graphql_errors_raise() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "boom"}]})

    try:
        _catalog(handler).search("tent", 5)
    except RuntimeError as exc:
        assert "boom" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError")


def test_order_methods_are_catalog_only() -> None:
    catalog = _catalog(lambda request: httpx.Response(200, json=_PAYLOAD))
    for call in (lambda: catalog.list_orders("c1"), lambda: catalog.get_order("c1", "o1")):
        try:
            call()
        except NotImplementedError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected NotImplementedError")
