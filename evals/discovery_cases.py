#!/usr/bin/env python3
"""Rule-generated discovery cases over OUR catalog (feature 046, discovery layer).

The correctness of every case is **derivable from the data** by a deterministic
rule, so the set cannot be hand-tuned to favour one retriever:

- ``title_substring`` — query is a distinctive n-gram of a product's title; the
  answer is that product (its title literally contains the n-gram).
- ``brand`` — query names a vendor; the answer is that vendor's products.
- ``category_price`` — query names a type and a budget taken from the data; the
  answer is the products of that type at or under the budget.
- ``color`` — query names a colour and a type; the answer is those products.

It measures **lexical/structured** matching on our catalog (a floor test); it does
**not** test semantic matching (that is what ESCI covers).

Run::

    uv run python evals/discovery_cases.py --per-rule 75 --rebuild
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
CASES = ROOT / "evals" / "discovery_cases.jsonl"
CATALOG = """
query($cursor: String) {
  products(first: 100, after: $cursor) {
    nodes {
      id title vendor productType tags
      variants(first: 1) { nodes { price } }
    }
    pageInfo { hasNextPage endCursor }
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


def fetch_products() -> list[dict]:
    """Fetch the real catalog snapshot from Shopify (cached under data/)."""
    if SNAPSHOT.exists():
        return json.loads(SNAPSHOT.read_text())
    import asyncio

    from app.adapters.shopify_client import ShopifyAdminClient
    from app.core.settings import load_settings

    _load_env()
    settings = load_settings()
    if not (settings.shopify.shop and settings.shopify.access_token):
        return []
    client = ShopifyAdminClient(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )

    async def _all() -> list[dict]:
        products: list[dict] = []
        cursor: str | None = None
        while True:
            data = await client.query(CATALOG, {"cursor": cursor})
            block = data["products"]
            for node in block["nodes"]:
                variants = node.get("variants", {}).get("nodes") or []
                price = float(variants[0]["price"]) if variants else 0.0
                products.append(
                    {
                        "id": node["id"],
                        "title": node["title"],
                        "vendor": node.get("vendor") or "",
                        "type": (node.get("productType") or "").replace("_", " "),
                        "tags": node.get("tags") or [],
                        "price": price,
                    }
                )
            if not block["pageInfo"]["hasNextPage"]:
                return products
            cursor = block["pageInfo"]["endCursor"]

    products = asyncio.run(_all())
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(products))
    return products


def _colour(product: dict) -> str:
    ignored = {product["type"], *product["tags"][:1]}
    for tag in product["tags"]:
        if tag not in ignored and not tag.startswith(("category:", "imported:")):
            return tag
    return ""


def generate(products: list[dict], per_rule: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    cases: list[dict] = []

    titled = [p for p in products if len(p["title"].split()) >= 3]
    for index, product in enumerate(rng.sample(titled, min(per_rule, len(titled)))):
        words = product["title"].split()
        start = rng.randrange(0, len(words) - 2)
        phrase = " ".join(words[start : start + 3])
        cases.append(
            {
                "case_id": f"rule-title-{index:03d}",
                "rule": "title_substring",
                "query": phrase,
                "expected_ids": [product["id"]],
            }
        )

    by_vendor: dict[str, list[str]] = {}
    for product in products:
        if product["vendor"] and product["vendor"] != "Unknown":
            by_vendor.setdefault(product["vendor"], []).append(product["id"])
    vendors = [v for v, ids in by_vendor.items() if len(ids) >= 1]
    for index, vendor in enumerate(rng.sample(vendors, min(per_rule, len(vendors)))):
        cases.append(
            {
                "case_id": f"rule-brand-{index:03d}",
                "rule": "brand",
                "query": f"{vendor} products",
                "expected_ids": by_vendor[vendor][:20],
            }
        )

    by_type: dict[str, list[dict]] = {}
    for product in products:
        if product["type"] and product["price"] > 0:
            by_type.setdefault(product["type"], []).append(product)
    types = [t for t, items in by_type.items() if len(items) >= 3]
    for index, product_type in enumerate(rng.sample(types, min(per_rule, len(types)))):
        items = by_type[product_type]
        budget = round(rng.choice(items)["price"], 2)
        expected = [p["id"] for p in items if p["price"] <= budget]
        if not expected:
            continue
        cases.append(
            {
                "case_id": f"rule-catprice-{index:03d}",
                "rule": "category_price",
                "query": f"{product_type} under ${budget:.2f}",
                "expected_ids": expected[:20],
            }
        )

    coloured = [p for p in products if _colour(p) and p["type"]]
    for index, product in enumerate(rng.sample(coloured, min(per_rule, len(coloured)))):
        colour = _colour(product)
        expected = [
            p["id"] for p in products if _colour(p) == colour and p["type"] == product["type"]
        ]
        cases.append(
            {
                "case_id": f"rule-colour-{index:03d}",
                "rule": "colour",
                "query": f"{colour} {product['type']}",
                "expected_ids": expected[:20],
            }
        )

    # De-duplicate by query: a repeated query (e.g. the same colour/type pair
    # sampled twice) would silently weight hit@10. Keep the first occurrence.
    unique: list[dict] = []
    seen: set[str] = set()
    for case in cases:
        key = " ".join(str(case["query"]).casefold().split())
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-rule", type=int, default=75)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    products = fetch_products()
    if not products:
        print("FAIL: no catalog snapshot (run with Shopify configured)")
        return 1
    print(f"catalog: {len(products)} products", flush=True)
    cases = generate(products, args.per_rule, args.seed)
    CASES.write_text("\n".join(json.dumps(case) for case in cases) + "\n")
    by_rule: dict[str, int] = {}
    for case in cases:
        by_rule[case["rule"]] = by_rule.get(case["rule"], 0) + 1
    print(f"cases: {len(cases)}  by rule: {by_rule}")
    print(f"wrote {CASES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
