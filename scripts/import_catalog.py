#!/usr/bin/env python3
"""Import a real product sample (Amazon Reviews'23) into the Shopify store (046).

Streams each category's item-metadata file and stops as soon as it has enough
products with a price, then creates them via the Admin GraphQL ``productSet``
mutation. Idempotent: a product whose SKU already exists is skipped, so the import
can be interrupted and resumed.

Usage::

    uv run python scripts/import_catalog.py --per-category 100
    uv run python scripts/import_catalog.py --dry-run
    uv run python scripts/import_catalog.py --categories Sports_and_Outdoors
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import zlib
from pathlib import Path

import httpx

from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError
from app.core.settings import load_settings

BASE = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories"
TAG = "imported:reviews23"
PROGRESS = Path("data/catalog/import_progress.json")

CATEGORIES = [
    "All_Beauty",
    "Amazon_Fashion",
    "Beauty_and_Personal_Care",
    "Appliances",
    "Arts_Crafts_and_Sewing",
    "Automotive",
    "Baby_Products",
    "Books",
    "CDs_and_Vinyl",
    "Cell_Phones_and_Accessories",
    "Clothing_Shoes_and_Jewelry",
    "Electronics",
    "Grocery_and_Gourmet_Food",
    "Handmade_Products",
    "Health_and_Household",
    "Health_and_Personal_Care",
    "Home_and_Kitchen",
    "Industrial_and_Scientific",
    "Movies_and_TV",
    "Musical_Instruments",
    "Office_Products",
    "Patio_Lawn_and_Garden",
    "Pet_Supplies",
    "Software",
    "Sports_and_Outdoors",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
    "Video_Games",
]

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


def _load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _log(message: str) -> None:
    print(message, flush=True)


def _stream_products(category: str, need: int) -> list[dict]:
    """Stream one category's metadata and return up to ``need`` priced products."""
    url = f"{BASE}/meta_{category}.jsonl.gz"
    items: list[dict] = []
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    buffer = b""
    with httpx.stream("GET", url, timeout=180, follow_redirects=True) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes():
            buffer += decompressor.decompress(chunk)
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                price = record.get("price")
                title = record.get("title")
                if not title or not isinstance(price, (int, float)) or price <= 0:
                    continue
                details = record.get("details") or {}
                items.append(
                    {
                        "asin": record.get("parent_asin") or record.get("asin"),
                        "title": str(title)[:180],
                        "price": round(float(price), 2),
                        "brand": str(record.get("store") or details.get("Brand") or "")[:80],
                        "category": category,
                        "color": str(details.get("Color") or "")[:40],
                        "rating": record.get("average_rating"),
                        "rating_number": record.get("rating_number"),
                        "features": [str(x)[:200] for x in (record.get("features") or [])][:5],
                    }
                )
                if len(items) >= need:
                    return items
    return items


def _input(product: dict) -> dict:
    features = "\n".join(f"<li>{f}</li>" for f in product.get("features", []))
    tags = [TAG, f"category:{product['category']}", product["category"]]
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


async def _import_product(
    client: ShopifyAdminClient,
    product: dict,
    existing: set[str],
    sem: asyncio.Semaphore,
    counters: dict[str, int],
) -> None:
    async with sem:
        if product["asin"] in existing:
            counters["skipped"] += 1
            return
        for attempt in range(3):
            try:
                result = await client.query(PRODUCT_SET, {"input": _input(product)})
                errors = result["productSet"]["userErrors"]
                if errors:
                    counters["failed"] += 1
                    _log(f"    error {product['asin']}: {errors[0].get('message')}")
                else:
                    counters["created"] += 1
                return
            except (ShopifyError, httpx.HTTPError) as exc:
                if attempt == 2:
                    counters["failed"] += 1
                    _log(f"    fail {product['asin']}: {str(exc)[:100]}")
                else:
                    await asyncio.sleep(1.0 * (attempt + 1))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-category", type=int, default=100)
    parser.add_argument("--categories", default="")
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",") if c.strip()] or CATEGORIES
    _load_env()
    settings = load_settings()
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    existing = await _existing_skus(client)
    _log(
        f"categories={len(categories)} per_category={args.per_category} "
        f"existing_skus={len(existing)} dry_run={args.dry_run}"
    )

    started = time.time()
    counters = {"created": 0, "skipped": 0, "failed": 0}
    sem = asyncio.Semaphore(args.concurrency)
    for index, category in enumerate(categories, 1):
        products = await asyncio.to_thread(_stream_products, category, args.per_category)
        _log(f"[{index}/{len(categories)}] {category}: streamed {len(products)} products")
        if args.dry_run:
            counters["created"] += len(products)
        else:
            await asyncio.gather(
                *(_import_product(client, product, existing, sem, counters) for product in products)
            )
        PROGRESS.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS.write_text(
            json.dumps(
                {
                    "category": category,
                    "done_categories": index,
                    "total_categories": len(categories),
                    **counters,
                    "elapsed_s": round(time.time() - started, 1),
                },
                indent=1,
            )
        )
        _log(
            f"    → created={counters['created']} skipped={counters['skipped']} "
            f"failed={counters['failed']} elapsed={time.time() - started:.0f}s"
        )

    _log(
        f"done: created={counters['created']} skipped={counters['skipped']} "
        f"failed={counters['failed']}"
    )
    return 1 if counters["failed"] else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
