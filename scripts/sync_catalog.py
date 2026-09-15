#!/usr/bin/env python3
"""Sync the live Shopify catalog into a local index snapshot (feature 046, step A1).

The live discovery path retrieves **locally** (see ``app/adapters/catalog_index.py``),
so it needs a local copy of the catalog's *documents*. Prices and stock are **not**
taken from here: the search path fetches the live product by id, so this file is
only the retrieval index, never a source of facts.

``data/`` is gitignored; run this once per catalog change.

Usage::

    uv run python scripts/sync_catalog.py            # fetch and write
    uv run python scripts/sync_catalog.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.shopify_client import ShopifyAdminClient  # noqa: E402
from app.core.settings import load_settings  # noqa: E402

SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
PAGE = 250
TAG = re.compile(r"<[^>]+>")


LIST_PRODUCTS = """
query ListProducts($n: Int!, $after: String) {
  products(first: $n, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      vendor
      productType
      tags
      descriptionHtml
      variants(first: 1) { nodes { price sku } }
    }
  }
}
"""


def _load_env(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _plain(description_html: str) -> str:
    """Flatten the product's description HTML into one searchable line."""
    text = TAG.sub(" ", description_html or "")
    return " ".join(html.unescape(text).split())


def _record(node: dict[str, Any]) -> dict[str, Any]:
    variants = (node.get("variants") or {}).get("nodes") or []
    price = float((variants[0] or {}).get("price", 0) or 0) if variants else 0.0
    sku = str(((variants[0] if variants else {}) or {}).get("sku") or "")
    return {
        "id": node["id"],
        # The source ASIN: the key the review store uses (step C/D).
        "sku": sku,
        "title": node.get("title") or "",
        "vendor": node.get("vendor") or "",
        # Shopify stores the Amazon category taxonomy with underscores
        # ("Beauty_and_Personal_Care"); the same convention as
        # evals/discovery_cases.py, so the document text matches the existing
        # corpus (and its embedding cache) exactly.
        "type": (node.get("productType") or "").replace("_", " "),
        "tags": list(node.get("tags") or []),
        "price": price,
        # Stored for the enriched-document step; not used by the tfidf document.
        "description": _plain(node.get("descriptionHtml") or ""),
    }


async def fetch_all(client: ShopifyAdminClient) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = await client.query(LIST_PRODUCTS, {"n": PAGE, "after": cursor})
        block = data.get("products") or {}
        nodes = block.get("nodes") or []
        products.extend(_record(node) for node in nodes)
        print(f"  fetched {len(products)} products", flush=True)
        page = block.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return products
        cursor = page.get("endCursor")
        if not cursor:
            return products


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _load_env()
    settings = load_settings()
    if not settings.shopify.shop or not settings.shopify.access_token:
        print("FAIL: SHOPIFY_SHOP / SHOPIFY_ACCESS_TOKEN are not set")
        return 1
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    products = await fetch_all(client)
    with_description = sum(1 for p in products if p["description"])
    print(
        f"catalog: {len(products)} products, {with_description} with a description, "
        f"{sum(1 for p in products if p['price'] > 0)} priced"
    )
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(products, ensure_ascii=False) + "\n")
    print(f"wrote {SNAPSHOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
