#!/usr/bin/env python3
"""Import a small real-product sample into the Shopify store (feature 046).

Reads ``data/catalog/reviews23_sample.json`` (a subset of Amazon Reviews'23 item
metadata: real titles, prices, brands, categories) and creates the products in the
dev store via the Admin GraphQL ``productSet`` mutation. Idempotent: a product
whose SKU already exists is skipped.

Usage::

    uv run python scripts/import_catalog.py --limit 300
    uv run python scripts/import_catalog.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError

SAMPLE = Path("data/catalog/reviews23_sample.json")
TAG = "imported:reviews23"

PRODUCT_SET = """
mutation($input: ProductSetInput!) {
  productSet(input: $input) {
    product { id title }
    userErrors { field message }
  }
}
"""

SKUS = """
query($cursor: String) {
  productVariants(first: 100, after: $cursor) {
    nodes { sku }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def _load_env(path: Path = Path(".env")) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"')
    return env


async def _existing_skus(client: ShopifyAdminClient) -> set[str]:
    skus: set[str] = set()
    cursor: str | None = None
    while True:
        data = await client.query(SKUS, {"cursor": cursor})
        block = data["productVariants"]
        for node in block["nodes"]:
            if node.get("sku"):
                skus.add(node["sku"])
        if not block["pageInfo"]["hasNextPage"]:
            return skus
        cursor = block["pageInfo"]["endCursor"]


def _input(product: dict) -> dict:
    features = "\n".join(f"<li>{f}</li>" for f in product.get("features", []))
    tags = [TAG, product["category"]]
    if product.get("color"):
        tags.append(product["color"])
    return {
        "title": product["title"],
        "vendor": product.get("brand") or "Unknown",
        "productType": product["category"],
        "tags": tags,
        "descriptionHtml": f"<ul>{features}</ul>" if features else "",
        "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
        "variants": [
            {
                "optionValues": [{"optionName": "Title", "name": "Default Title"}],
                "price": f"{product['price']:.2f}",
                "sku": product["asin"],
                "inventoryItem": {"tracked": False},
            }
        ],
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = _load_env()
    shop, token = env.get("SHOPIFY_SHOP", ""), env.get("SHOPIFY_ACCESS_TOKEN", "")
    if not shop or not token:
        print("FAIL: SHOPIFY_SHOP / SHOPIFY_ACCESS_TOKEN missing in .env")
        return 1

    products = json.loads(SAMPLE.read_text())[: args.limit]
    client = ShopifyAdminClient(shop, token, env.get("SHOPIFY_API_VERSION", "2025-07"))
    existing = await _existing_skus(client)
    print(f"sample={len(products)} existing_skus={len(existing)} dry_run={args.dry_run}")

    created = skipped = failed = 0
    for product in products:
        if product["asin"] in existing:
            skipped += 1
            continue
        if args.dry_run:
            created += 1
            continue
        try:
            result = await client.query(PRODUCT_SET, {"input": _input(product)})
            errors = result["productSet"]["userErrors"]
            if errors:
                failed += 1
                print(f"  error {product['asin']}: {errors[0].get('message')}")
            else:
                created += 1
        except ShopifyError as exc:
            failed += 1
            print(f"  fail {product['asin']}: {str(exc)[:120]}")
        throttle = (client.last_cost or {}).get("throttleStatus", {})
        if throttle.get("currentlyAvailable", 1000) < 200:
            await asyncio.sleep(2)
        if (created + skipped + failed) % 50 == 0:
            print(f"  … {created} created, {skipped} skipped, {failed} failed")

    print(f"done: created={created} skipped={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
