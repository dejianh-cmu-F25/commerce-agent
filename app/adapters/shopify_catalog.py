"""Catalog adapter backed by the Shopify Admin API (feature 046).

Reads the real product catalog imported from Amazon Reviews'23 (see
``scripts/import_catalog.py``). This adapter is **catalog-only**: it implements
``search``/``get`` and raises for order methods (orders are owned by the
post-purchase adapter). It is synchronous because the ``StorefrontBackend`` port
is synchronous; the transport is a thin ``httpx.Client`` so tests run keylessly
with a ``MockTransport``.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.types import Product

SEARCH = """
query($q: String!, $n: Int!) {
  products(first: $n, query: $q) {
    nodes {
      id
      title
      tags
      variants(first: 1) { nodes { sku price inventoryQuantity inventoryItem { tracked } } }
    }
  }
}
"""

GET = """
query($id: ID!) {
  product(id: $id) {
    id
    title
    tags
    variants(first: 1) { nodes { sku price inventoryQuantity inventoryItem { tracked } } }
  }
}
"""


class ShopifyCatalog:
    """A read-only product catalog over one shop's Admin API."""

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
            raise ValueError("Shopify shop/access_token is empty")
        self._url = f"https://{shop}/admin/api/{api_version}/graphql.json"
        self._headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self._client = client or httpx.Client(timeout=timeout)

    def _query(self, graphql: str, variables: dict[str, Any]) -> dict:
        response = self._client.post(
            self._url, json={"query": graphql, "variables": variables}, headers=self._headers
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise RuntimeError(f"Shopify GraphQL errors: {body['errors']}")
        return body["data"]

    def search(self, query: str, limit: int, *, evidence: bool = False) -> list[Product]:
        # One index, so the query class does not change the answer.
        del evidence
        if not query.strip() or limit <= 0:
            return []
        data = self._query(SEARCH, {"q": query, "n": limit})
        return [_product(node) for node in data["products"]["nodes"]]

    def get(self, product_id: str) -> Product | None:
        data = self._query(GET, {"id": product_id})
        node = data.get("product")
        return _product(node) if node else None

    def list_orders(self, customer_id: str) -> list[Any]:
        raise NotImplementedError("ShopifyCatalog is catalog-only; use the post-purchase adapter")

    def get_order(self, customer_id: str, order_id: str) -> Any:
        raise NotImplementedError("ShopifyCatalog is catalog-only; use the post-purchase adapter")


def _product(node: dict) -> Product:
    variants = node.get("variants", {}).get("nodes", [])
    first = variants[0] if variants else {}
    try:
        price = float(first.get("price", 0) or 0)
    except (TypeError, ValueError):
        price = 0.0
    # Reviews'23 carries no stock; imported products use untracked inventory, which
    # means "available". A tracked product reports its real quantity.
    tracked = (first.get("inventoryItem") or {}).get("tracked")
    stock = int(first.get("inventoryQuantity") or 0) if tracked else 1
    return Product(
        id=str(node["id"]),
        title=str(node["title"]),
        price=price,
        stock=stock,
        tags=[str(tag) for tag in node.get("tags", [])],
        sku=str(first.get("sku") or ""),
    )
