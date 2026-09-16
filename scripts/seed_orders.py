#!/usr/bin/env python3
"""Create demo orders from the **real imported products** (feature 046).

Orders are inherently private, so they are generated — but they reference the real
imported catalog and use the **real Shopify fulfillment lifecycle**::

    orderCreate -> fulfillmentCreate -> fulfillmentEventCreate(DELIVERED)

The mix is configurable: delivered (fulfilled + delivery event), in-transit
(fulfilled, no delivery event), processing (unfulfilled).

Usage::

    uv run python scripts/seed_orders.py --reset
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError
from app.core.settings import load_settings

VARIANTS = """
{ products(first: 30, sortKey: CREATED_AT, reverse: true) {
    nodes { title variants(first: 1) { nodes { id } } } } }
"""

ORDER_CREATE = """
mutation($order: OrderCreateOrderInput!) {
  orderCreate(order: $order) { order { id name } userErrors { field message } }
}
"""

FULFILLMENT_ORDERS = """
query($id: ID!) {
  order(id: $id) {
    fulfillmentOrders(first: 5) {
      nodes { id status lineItems(first: 20) { nodes { id remainingQuantity } } }
    }
  }
}
"""

FULFILLMENT_CREATE = """
mutation($f: FulfillmentInput!) {
  fulfillmentCreate(fulfillment: $f) {
    fulfillment { id deliveredAt }
    userErrors { field message }
  }
}
"""

EVENT_CREATE = """
mutation($e: FulfillmentEventInput!) {
  fulfillmentEventCreate(fulfillmentEvent: $e) {
    fulfillmentEvent { id status happenedAt }
    userErrors { field message }
  }
}
"""


def _load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _log(message: str) -> None:
    print(message, flush=True)


async def _delete_all_orders(client: ShopifyAdminClient) -> int:
    data = await client.query("{ orders(first: 100) { nodes { id name } } }")
    deleted = 0
    for order in data["orders"]["nodes"]:
        try:
            await client.query(
                "mutation($id:ID!){ orderDelete(orderId:$id){ deletedId userErrors{message} } }",
                {"id": order["id"]},
            )
            deleted += 1
        except ShopifyError as exc:
            _log(f"  delete failed {order['name']}: {str(exc)[:100]}")
    return deleted


async def _real_variants(client: ShopifyAdminClient) -> list[str]:
    data = await client.query(VARIANTS)
    variants = [
        product["variants"]["nodes"][0]["id"]
        for product in data["products"]["nodes"]
        if product["variants"]["nodes"]
    ]
    return variants


async def _create_order(client: ShopifyAdminClient, variant_id: str, email: str) -> str | None:
    result = await client.query(
        ORDER_CREATE,
        {
            "order": {
                "lineItems": [{"variantId": variant_id, "quantity": 1}],
                "email": email,
                "financialStatus": "PAID",
            }
        },
    )
    errors = result["orderCreate"].get("userErrors") or []
    if errors:
        _log(f"  orderCreate error: {errors[0].get('message')}")
        return None
    return str(result["orderCreate"]["order"]["id"])


async def _fulfill(client: ShopifyAdminClient, order_id: str) -> str | None:
    data = await client.query(FULFILLMENT_ORDERS, {"id": order_id})
    orders = data["order"]["fulfillmentOrders"]["nodes"]
    line_items = [
        {
            "fulfillmentOrderId": fo["id"],
            "fulfillmentOrderLineItems": [
                {"id": li["id"], "quantity": li["remainingQuantity"]}
                for li in fo["lineItems"]["nodes"]
            ],
        }
        for fo in orders
    ]
    if not line_items:
        return None
    result = await client.query(
        FULFILLMENT_CREATE,
        {
            "f": {
                "lineItemsByFulfillmentOrder": line_items,
                "trackingInfo": {"company": "USPS", "number": "9400100000000000000000"},
                "notifyCustomer": False,
            }
        },
    )
    errors = result["fulfillmentCreate"].get("userErrors") or []
    if errors:
        _log(f"  fulfillmentCreate error: {errors[0].get('message')}")
        return None
    return str(result["fulfillmentCreate"]["fulfillment"]["id"])


async def _mark_delivered(client: ShopifyAdminClient, fulfillment_id: str, days_ago: int) -> bool:
    happened_at = (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()
    result = await client.query(
        EVENT_CREATE,
        {"e": {"fulfillmentId": fulfillment_id, "status": "DELIVERED", "happenedAt": happened_at}},
    )
    errors = result["fulfillmentEventCreate"].get("userErrors") or []
    if errors:
        _log(f"  event error: {errors[0].get('message')}")
        return False
    return True


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivered", type=int, default=3)
    parser.add_argument("--in-transit", type=int, default=2)
    parser.add_argument("--processing", type=int, default=1)
    parser.add_argument("--email", default="demo.customer@example.com")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    _load_env()
    settings = load_settings()
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    if args.reset:
        _log(f"deleted orders: {await _delete_all_orders(client)}")

    variants = await _real_variants(client)
    if not variants:
        _log("FAIL: no imported products found")
        return 1

    plan = (
        [("delivered", 7)] * args.delivered
        + [("in-transit", 0)] * args.in_transit
        + [("processing", 0)] * args.processing
    )
    created = 0
    for index, (state, days_ago) in enumerate(plan):
        order_id = await _create_order(client, variants[index % len(variants)], args.email)
        if not order_id:
            continue
        fulfillment_id = None
        if state in ("delivered", "in-transit"):
            fulfillment_id = await _fulfill(client, order_id)
        delivered = state == "delivered" and fulfillment_id is not None
        if delivered:
            await _mark_delivered(client, fulfillment_id, days_ago)
        created += 1
        _log(f"  {state:11s} created (delivered={delivered})")
    _log(f"orders created: {created}")
    return 0 if created else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
