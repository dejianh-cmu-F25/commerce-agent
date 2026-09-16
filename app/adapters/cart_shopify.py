"""Shopify Storefront cart (Service Provider for :class:`app.ports.cart.CartBackend`).

The Storefront API is a different surface from the Admin API: it is what a storefront
uses, it authenticates with a **Storefront access token** (not the Admin token), and it
takes **variant** ids rather than product ids. This provider is opt-in
(``cart.provider: shopify_storefront``) because it writes a real cart in the store.

**Not live-verified.** It needs `SHOPIFY_STOREFRONT_TOKEN`, which this project's store
does not have (see `docs/shopify-setup.md`); the mapping and the request shapes are
covered by tests against a MockTransport, and the live path is untested until a token
exists. That is stated rather than implied.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.session import CartLine, Session
from app.core.types import Product

_CART_FIELDS = """
      id
      checkoutUrl
      lines(first: 100) {
        nodes {
          quantity
          merchandise {
            ... on ProductVariant {
              id
              price { amount }
              product { id title }
            }
          }
        }
      }
"""

CART_CREATE = f"""
mutation CreateCart($lines: [CartLineInput!]) {{
  cartCreate(input: {{lines: $lines}}) {{
    cart {{{_CART_FIELDS}}}
    userErrors {{ field message }}
  }}
}}
"""

CART_LINES_ADD = f"""
mutation AddLines($cartId: ID!, $lines: [CartLineInput!]!) {{
  cartLinesAdd(cartId: $cartId, lines: $lines) {{
    cart {{{_CART_FIELDS}}}
    userErrors {{ field message }}
  }}
}}
"""

CART_GET = f"""
query GetCart($cartId: ID!) {{
  cart(id: $cartId) {{{_CART_FIELDS}}}
}}
"""


class CartError(RuntimeError):
    """A Storefront cart call failed (an HTTP error, or the API's userErrors)."""


def _lines(cart: dict[str, Any]) -> list[CartLine]:
    nodes = ((cart or {}).get("lines") or {}).get("nodes") or []
    lines: list[CartLine] = []
    for node in nodes:
        variant = node.get("merchandise") or {}
        product = variant.get("product") or {}
        lines.append(
            CartLine(
                product_id=str(product.get("id") or variant.get("id") or ""),
                title=str(product.get("title") or ""),
                quantity=int(node.get("quantity") or 0),
                unit_price=float((variant.get("price") or {}).get("amount") or 0.0),
            )
        )
    return lines


class ShopifyStorefrontCart:
    """A real cart per session, keyed by the session id.

    The cart id lives in this adapter rather than on the session, so the session
    persistence contract is untouched; a restart therefore starts a new cart, which is
    the honest behaviour for a simulated storefront and is stated here.
    """

    def __init__(
        self,
        shop: str,
        access_token: str,
        api_version: str = "2025-07",
        *,
        client: httpx.Client | None = None,
        timeout: float = 20.0,
    ) -> None:
        if not shop or not access_token:
            raise ValueError(
                "Storefront shop/token is empty; set SHOPIFY_SHOP and SHOPIFY_STOREFRONT_TOKEN"
            )
        self._url = f"https://{shop}/api/{api_version}/graphql.json"
        self._headers = {
            "X-Shopify-Storefront-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self._client = client or httpx.Client(timeout=timeout)
        self._carts: dict[str, str] = {}

    def _query(self, graphql: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(
            self._url, json={"query": graphql, "variables": variables}, headers=self._headers
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise CartError(f"Storefront GraphQL errors: {body['errors']}")
        return body.get("data") or {}

    @staticmethod
    def _unpack(payload: dict[str, Any], key: str) -> dict[str, Any]:
        block = payload.get(key) or {}
        errors = block.get("userErrors") or []
        if errors:
            raise CartError(f"{key} rejected: {errors}")
        return block.get("cart") or {}

    def add(self, session: Session, product: Product, quantity: int) -> None:
        if not product.variant_id:
            raise CartError(f"product {product.id} has no variant id; a cart holds variants")
        line = {"merchandiseId": product.variant_id, "quantity": quantity}
        cart_id = self._carts.get(session.id)
        if cart_id is None:
            data = self._query(CART_CREATE, {"lines": [line]})
            cart = self._unpack(data, "cartCreate")
        else:
            data = self._query(CART_LINES_ADD, {"cartId": cart_id, "lines": [line]})
            cart = self._unpack(data, "cartLinesAdd")
        new_id = str(cart.get("id") or "")
        if not new_id:
            raise CartError("the Storefront API returned a cart with no id")
        self._carts[session.id] = new_id
        # The session stays the transcript's view of the cart, so the UI and the
        # persistence layer keep working unchanged.
        session.cart = _lines(cart)

    def view(self, session: Session) -> list[CartLine]:
        cart_id = self._carts.get(session.id)
        if cart_id is None:
            return list(session.cart)
        cart = self._query(CART_GET, {"cartId": cart_id}).get("cart") or {}
        session.cart = _lines(cart)
        return list(session.cart)
