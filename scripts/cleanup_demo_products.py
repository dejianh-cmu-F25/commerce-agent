#!/usr/bin/env python3
"""Remove the Shopify demo (fabricated) data (feature 046).

Deletes products **not** tagged ``imported:reviews23`` (the dev store's generated
demo catalog) and the demo order(s). Everything that remains is real imported data.

Usage::

    uv run python scripts/cleanup_demo_products.py --dry-run
    uv run python scripts/cleanup_demo_products.py
    uv run python scripts/cleanup_demo_products.py --keep-orders
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError
from app.core.settings import load_settings

TAG = "imported:reviews23"


def _load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _client() -> ShopifyAdminClient:
    _load_env()
    settings = load_settings()
    return ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )


async def _all_products(client: ShopifyAdminClient) -> list[dict]:
    products: list[dict] = []
    cursor: str | None = None
    while True:
        data = await client.query(
            "query($cursor:String){ products(first:100, after:$cursor){"
            " nodes{id title tags} pageInfo{hasNextPage endCursor} } }",
            {"cursor": cursor},
        )
        block = data["products"]
        products.extend(block["nodes"])
        if not block["pageInfo"]["hasNextPage"]:
            return products
        cursor = block["pageInfo"]["endCursor"]


async def _all_orders(client: ShopifyAdminClient) -> list[dict]:
    data = await client.query("{ orders(first:50){ nodes{id name} } }")
    return data["orders"]["nodes"]


async def _delete_product(client: ShopifyAdminClient, product_id: str) -> str | None:
    result = await client.query(
        "mutation($id:ID!){ productDelete(input:{id:$id}){"
        " deletedProductId userErrors{message} } }",
        {"id": product_id},
    )
    errors = result["productDelete"].get("userErrors") or []
    return errors[0]["message"] if errors else None


async def _delete_order(client: ShopifyAdminClient, order_id: str) -> str | None:
    last_error: str | None = None
    for mutation in (
        "mutation($id:ID!){ orderDelete(orderId:$id){ deletedId userErrors{message} } }",
        "mutation($id:ID!){ orderDelete(input:{id:$id}){ deletedId userErrors{message} } }",
    ):
        try:
            result = await client.query(mutation, {"id": order_id})
        except ShopifyError as exc:
            last_error = str(exc)[:160]
            continue
        block = next(iter(result.values()))
        errors = block.get("userErrors") or []
        if errors:
            last_error = errors[0]["message"]
            continue
        return None
    return last_error or "no mutation worked"


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-orders", action="store_true")
    args = parser.parse_args()

    client = _client()
    fabricated = [p for p in await _all_products(client) if TAG not in (p.get("tags") or [])]
    orders = [] if args.keep_orders else await _all_orders(client)
    print(f"fabricated products: {len(fabricated)}  orders: {[o['name'] for o in orders]}")
    for product in fabricated:
        print(f"  - {product['title'][:60]}")
    if args.dry_run:
        print("dry run: nothing deleted")
        return 0

    deleted = 0
    for product in fabricated:
        try:
            error = await _delete_product(client, product["id"])
        except ShopifyError as exc:
            error = str(exc)[:120]
        if error:
            print(f"  error {product['title'][:40]}: {error}")
        else:
            deleted += 1
    print(f"deleted products: {deleted}/{len(fabricated)}")

    for order in orders:
        error = await _delete_order(client, order["id"])
        print(f"  order {order['name']}: {'ok' if not error else error}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
