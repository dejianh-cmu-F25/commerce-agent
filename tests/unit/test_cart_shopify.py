"""The Storefront cart: request shapes and mapping, against a MockTransport.

The live path needs a Storefront access token this project does not have, so the
adapter is verified here and labelled unverified-live in docs/shopify-setup.md.
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.adapters.cart_shopify import CartError, ShopifyStorefrontCart
from app.core.session import Session
from app.core.types import Product

CART_NODE = {
    "id": "gid://shopify/Cart/1",
    "checkoutUrl": "https://shop.example/checkout/1",
    "lines": {
        "nodes": [
            {
                "quantity": 2,
                "merchandise": {
                    "id": "gid://shopify/ProductVariant/11",
                    "price": {"amount": "24.50"},
                    "product": {"id": "gid://shopify/Product/1", "title": "2-Person Tent"},
                },
            }
        ]
    },
}


def _cart(handler) -> ShopifyStorefrontCart:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ShopifyStorefrontCart("test.myshopify.com", "storefront-token", client=client)


PRODUCT = Product(
    id="gid://shopify/Product/1",
    title="2-Person Tent",
    price=24.5,
    stock=1,
    variant_id="gid://shopify/ProductVariant/11",
)


def test_the_first_add_creates_a_cart_with_the_variant() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(body)
        return httpx.Response(
            200, json={"data": {"cartCreate": {"cart": CART_NODE, "userErrors": []}}}
        )

    cart = _cart(handler)
    session = Session(id="s")
    cart.add(session, PRODUCT, 2)

    assert seen[0]["variables"] == {"lines": [{"merchandiseId": PRODUCT.variant_id, "quantity": 2}]}
    # The lines are mirrored onto the session, so the transcript and the persistence
    # layer keep working unchanged.
    assert [(line.product_id, line.quantity, line.unit_price) for line in session.cart] == [
        ("gid://shopify/Product/1", 2, 24.5)
    ]


def test_a_second_add_targets_the_existing_cart() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        # "mutation CreateCart($lines: ...)" -> "CreateCart"
        operation = body["query"].split()[1].split("(")[0]
        calls.append(operation)
        key = {"CreateCart": "cartCreate", "AddLines": "cartLinesAdd"}[operation]
        return httpx.Response(200, json={"data": {key: {"cart": CART_NODE, "userErrors": []}}})

    cart = _cart(handler)
    session = Session(id="s")
    cart.add(session, PRODUCT, 1)
    cart.add(session, PRODUCT, 1)
    assert calls == ["CreateCart", "AddLines"]


def test_a_product_without_a_variant_is_refused() -> None:
    cart = _cart(lambda _r: httpx.Response(200, json={}))
    with pytest.raises(CartError, match="variant"):
        cart.add(Session(id="s"), Product(id="p", title="t", price=1.0, stock=1), 1)


def test_the_api_user_errors_are_raised_not_swallowed() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "cartCreate": {
                        "cart": None,
                        "userErrors": [{"field": "lines", "message": "nope"}],
                    }
                }
            },
        )

    with pytest.raises(CartError, match="cartCreate rejected"):
        _cart(handler).add(Session(id="s"), PRODUCT, 1)


def test_an_http_failure_is_raised() -> None:
    with pytest.raises(httpx.HTTPStatusError):
        _cart(lambda _r: httpx.Response(500, text="boom")).add(Session(id="s"), PRODUCT, 1)


def test_it_refuses_to_build_without_a_token() -> None:
    with pytest.raises(ValueError, match="STOREFRONT_TOKEN"):
        ShopifyStorefrontCart("test.myshopify.com", "")
