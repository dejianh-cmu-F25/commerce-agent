#!/usr/bin/env python3
"""Create demo orders from the **real imported products** (feature 046).

Orders are inherently private, so they are generated — but they reference the real
imported catalog. Each order is paid and fulfilled so the post-purchase journey
(WISMO, returns) has something to work with.

Usage::

    uv run python scripts/seed_orders.py --count 3
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError
from app.core.settings import load_settings

VARIANTS = """
{
  products(first: 20, sortKey: CREATED_AT, reverse: true) {
    nodes {
      title
      variants(first: 1) { nodes { id sku price } }
    }
  }
}
"""

ORDER_CREATE = """
mutation($order: OrderCreateOrderInput!) {
  orderCreate(order: $order) {
    order { id name displayFinancialStatus displayFulfillmentStatus }
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


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--email", default="demo.customer@example.com")
    args = parser.parse_args()

    _load_env()
    settings = load_settings()
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    data = await client.query(VARIANTS)
    products = [p for p in data["products"]["nodes"] if p["variants"]["nodes"]]
    if not products:
        print("FAIL: no imported products found")
        return 1
    # No read_locations scope: record the (generated) delivery date as an order
    # attribute instead of a fulfillment. The adapter reads it as a fallback.
    from datetime import UTC, datetime, timedelta

    delivered_at = (datetime.now(UTC) - timedelta(days=6)).isoformat()

    created = 0
    for index in range(args.count):
        product = products[index % len(products)]
        variant = product["variants"]["nodes"][0]
        payload = {
            "lineItems": [{"variantId": variant["id"], "quantity": 1}],
            "email": args.email,
            "financialStatus": "PAID",
            "customAttributes": [{"key": "delivered_at", "value": delivered_at}],
        }
        try:
            result = await client.query(ORDER_CREATE, {"order": payload})
        except ShopifyError as exc:
            print(f"  error: {str(exc)[:200]}")
            continue
        errors = result["orderCreate"].get("userErrors") or []
        if errors:
            print(f"  userError: {errors[0].get('message')} ({errors[0].get('field')})")
            continue
        order = result["orderCreate"]["order"]
        created += 1
        print(
            f"  created {order['name']} [{product['title'][:40]}] {order['displayFinancialStatus']}"
        )
    print(f"orders created: {created}")
    return 0 if created else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
