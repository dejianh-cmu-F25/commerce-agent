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
    fulfillments(first: 1) { deliveredAt }
    customer { id }
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

_ORDER_BY_NAME_QUERY = """
query GetOrderByName($q: String!) {
  orders(first: 1, query: $q) {
    nodes {
      id
      name
      createdAt
      displayFinancialStatus
      displayFulfillmentStatus
      totalPriceSet { shopMoney { amount currencyCode } }
      fulfillments(first: 1) { deliveredAt }
    customer { id }
    customAttributes { key value }
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


def _delivered_at(node: dict[str, Any]) -> str | None:
    """The fulfillment's real ``deliveredAt`` (set by a DELIVERED fulfillment event).

    ``None`` when the order is not delivered (in transit or unfulfilled); the
    engine escalates rather than guessing a window.
    """
    fulfillments = node.get("fulfillments") or []
    if isinstance(fulfillments, dict):
        fulfillments = fulfillments.get("nodes") or []
    fulfillment = fulfillments[0] if fulfillments else {}
    delivered = fulfillment.get("deliveredAt")
    return str(delivered) if delivered else None


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
        delivered_at=_delivered_at(node),
        customer_id=str((node.get("customer") or {}).get("id") or ""),
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
        # Accept a global id, or a human order number like "#1001" / "1001".
        if order_id and not order_id.startswith("gid://"):
            name = order_id.lstrip("#").strip()
            data = await self._client.query(_ORDER_BY_NAME_QUERY, {"q": f"name:#{name}"})
            nodes = (data.get("orders") or {}).get("nodes") or []
            return _to_order(nodes[0]) if nodes else None
        data = await self._client.query(_ORDER_QUERY, {"id": order_id})
        node = data.get("order")
        return _to_order(node) if node else None

    async def returnable_items(self, order_id: str) -> list[ReturnableItem]:
        # returnableFulfillments(orderId:) requires a global id, but callers hold a
        # human order number like "1006". Passing that straight through made Shopify
        # reject the query, the tool fail, and the agent retry with other id formats
        # (the source of the tool-call loops). Resolve to the real id first.
        if order_id and not order_id.startswith("gid://"):
            order = await self.get_order(order_id)
            if order is None:
                return []
            order_id = order.id
        data = await self._client.query(_RETURNABLE_QUERY, {"id": order_id, "first": 10})
        edges = (data.get("returnableFulfillments") or {}).get("edges") or []
        items: list[ReturnableItem] = []
        for edge in edges:
            line_edges = ((edge.get("node") or {}).get("returnableFulfillmentLineItems") or {}).get(
                "edges"
            ) or []
            items.extend(_to_returnable(line_edge["node"]) for line_edge in line_edges)
        return items
