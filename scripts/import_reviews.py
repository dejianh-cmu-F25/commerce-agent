#!/usr/bin/env python3
"""Import real product reviews (Amazon Reviews'23) into the local store (046).

For each category it finds the imported products' SKUs in Shopify, streams that
category's review file, and keeps the most helpful reviews per product. Idempotent:
products that already have reviews are skipped.

Usage::

    uv run python scripts/import_reviews.py --per-product 5
    uv run python scripts/import_reviews.py --categories Video_Games --reset
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import zlib
from collections import defaultdict
from pathlib import Path

import httpx

from app.adapters.reviews_sqlite import SqliteReviewStore
from app.adapters.shopify_client import ShopifyAdminClient
from app.core.settings import load_settings
from app.ports.reviews import Review

BASE = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories"
DEFAULT_DB = "data/reviews/reviews.sqlite"
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


def _load_env(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _log(message: str) -> None:
    print(message, flush=True)


async def _skus_for_query(client: ShopifyAdminClient, query: str) -> set[str]:
    skus: set[str] = set()
    cursor: str | None = None
    while True:
        data = await client.query(
            "query($q:String!,$cursor:String){ products(first:100, query:$q, after:$cursor){"
            " nodes{ variants(first:1){nodes{sku}} } pageInfo{hasNextPage endCursor} } }",
            {"q": query, "cursor": cursor},
        )
        block = data["products"]
        for node in block["nodes"]:
            for variant in node["variants"]["nodes"]:
                if variant.get("sku"):
                    skus.add(variant["sku"])
        if not block["pageInfo"]["hasNextPage"]:
            return skus
        cursor = block["pageInfo"]["endCursor"]


async def _skus_for_category(client: ShopifyAdminClient, category: str) -> set[str]:
    # The product type may be the underscored category or its spaced form.
    for query in (f"product_type:{category}", f'product_type:"{category.replace("_", " ")}"'):
        skus = await _skus_for_query(client, query)
        if skus:
            return skus
    return set()


def _stream_reviews(
    category: str, wanted: set[str], per_product: int, max_lines: int
) -> list[Review]:
    if not wanted:
        return []
    url = f"{BASE}/{category}.jsonl.gz"
    collected: dict[str, list[Review]] = defaultdict(list)
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    buffer = b""
    lines = 0
    with httpx.stream("GET", url, timeout=180, follow_redirects=True) as response:
        response.raise_for_status()
        for chunk in response.iter_bytes():
            buffer += decompressor.decompress(chunk)
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                lines += 1
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                asin = record.get("parent_asin") or record.get("asin")
                if asin not in wanted or len(collected[asin]) >= per_product:
                    continue
                collected[asin].append(
                    Review(
                        product_id=asin,
                        rating=float(record.get("rating") or 0),
                        title=str(record.get("title") or "")[:200],
                        text=str(record.get("text") or "")[:2000],
                        helpful_votes=int(
                            record.get("helpful_vote") or record.get("helpful_votes") or 0
                        ),
                        verified=bool(record.get("verified_purchase")),
                        timestamp_ms=int(record.get("timestamp") or 0),
                    )
                )
                if all(len(v) >= per_product for v in collected.values()) and len(collected) == len(
                    wanted
                ):
                    return [r for reviews in collected.values() for r in reviews]
                if lines >= max_lines:
                    return [r for reviews in collected.values() for r in reviews]
    return [r for reviews in collected.values() for r in reviews]


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-product", type=int, default=5)
    parser.add_argument("--categories", default="")
    parser.add_argument("--max-lines", type=int, default=1_500_000)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",") if c.strip()] or CATEGORIES
    _load_env()
    settings = load_settings()
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    store = SqliteReviewStore(args.db)
    if args.reset:
        Path(args.db).unlink(missing_ok=True)
        store = SqliteReviewStore(args.db)
    _log(f"categories={len(categories)} per_product={args.per_product} existing={store.count()}")

    started = time.time()
    total = 0
    for index, category in enumerate(categories, 1):
        skus = await _skus_for_category(client, category)
        already = {s for s in skus if store.get_reviews(s, 1)}
        wanted = skus - already
        reviews = await asyncio.to_thread(
            _stream_reviews, category, wanted, args.per_product, args.max_lines
        )
        added = store.add(reviews)
        total += added
        _log(
            f"[{index}/{len(categories)}] {category}: skus={len(skus)} new_skus={len(wanted)} "
            f"reviews+={added} total={store.count()} elapsed={time.time() - started:.0f}s"
        )
    _log(f"done: +{total} reviews, store={store.count()}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
