"""Shopify post-purchase reads (feature 045, read-only phase).

Implements :class:`app.ports.post_purchase.PostPurchaseBackend` against the
Shopify Admin GraphQL API: order reads and returnable fulfillments. Writes (a
return request) land in phase 3 and are gated by the harness.
"""

from __future__ import annotations

from typing import Any

from app.adapters.shopify_client import ShopifyAdminClient
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem

_ORDER_QUERY = """
query GetOrder($id: ID!) {
  order(id: $id) {
    id
    name
    createdAt
    displayFinancialStatus
    displayFulfillmentStatus
    totalPriceSet { shopMoney { amount currencyCode } }
    lineItems(first: 50) {
      nodes {
        id
        name
        quantity
        sku
        originalUnitPriceSet { shopMoney { amount currencyCode } }
      }
    }
  }
}
"""

_RETURNABLE_QUERY = """
query Returnable($id: ID!, $first: Int!) {
  returnableFulfillments(orderId: $id, first: $first) {
    edges {
      node {
        id
        returnableFulfillmentLineItems(first: 50) {
          edges {
            node {
              quantity
              fulfillmentLineItem { id lineItem { name sku } }
            }
          }
        }
      }
    }
  }
}
"""


def _money(bag: dict | None) -> tuple[float, str]:
    money = (bag or {}).get("shopMoney") or {}
    return float(money.get("amount", 0.0)), str(money.get("currencyCode", ""))


def _to_order(node: dict[str, Any]) -> OrderView:
    total, currency = _money(node.get("totalPriceSet"))
    nodes = (node.get("lineItems") or {}).get("nodes") or []
    return OrderView(
        id=str(node.get("id", "")),
        name=str(node.get("name", "")),
        created_at=str(node.get("createdAt", "")),
        financial_status=str(node.get("displayFinancialStatus", "")),
        fulfillment_status=str(node.get("displayFulfillmentStatus", "")),
        total=total,
        currency=currency,
        line_items=[
            LineItem(
                id=str(item.get("id", "")),
                title=str(item.get("name", "")),
                quantity=int(item.get("quantity", 0)),
                sku=str(item.get("sku") or ""),
            )
            for item in nodes
        ],
    )


def _to_returnable(node: dict[str, Any]) -> ReturnableItem:
    fulfillment_line_item = node.get("fulfillmentLineItem") or {}
    line = fulfillment_line_item.get("lineItem") or {}
    return ReturnableItem(
        fulfillment_line_item_id=str(fulfillment_line_item.get("id", "")),
        title=str(line.get("name", "")),
        sku=str(line.get("sku") or ""),
        quantity=int(node.get("quantity", 0)),
    )


class ShopifyPostPurchase:
    """Reads orders and returnable items from the Shopify Admin API."""

    def __init__(self, client: ShopifyAdminClient) -> None:
        self._client = client

    async def get_order(self, order_id: str) -> OrderView | None:
        data = await self._client.query(_ORDER_QUERY, {"id": order_id})
        node = data.get("order")
        return _to_order(node) if node else None

    async def returnable_items(self, order_id: str) -> list[ReturnableItem]:
        data = await self._client.query(_RETURNABLE_QUERY, {"id": order_id, "first": 10})
        edges = (data.get("returnableFulfillments") or {}).get("edges") or []
        items: list[ReturnableItem] = []
        for edge in edges:
            line_edges = ((edge.get("node") or {}).get("returnableFulfillmentLineItems") or {}).get(
                "edges"
            ) or []
            items.extend(_to_returnable(line_edge["node"]) for line_edge in line_edges)
        return items
