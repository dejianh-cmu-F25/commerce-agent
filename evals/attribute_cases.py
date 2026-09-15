#!/usr/bin/env python3
"""Attribute queries whose labels come from review text (feature 046, step E).

The rule set is lexical: brand + type, colour + type, a title substring, a price
ceiling. Enriching product documents with reviews and features *hurt* it (measured:
tfidf hit@10 0.991 -> 0.954), which is expected - it makes documents longer and adds
vocabulary a keyword query never asked for. What enrichment is *for* is a different
query class: attributes that no title states.

An attribute query here is "a <type> that reviewers say is <phrase>". The label is not
my judgement: the product is the true positive because **its own review text contains
that phrase**, which the generator checks. A title-only index cannot satisfy the query
- the phrase is not in any title - so the pair (plain, enriched) measures exactly the
capability enrichment adds.

Run::

    uv run python evals/attribute_cases.py            # report
    uv run python evals/attribute_cases.py --write    # write evals/attribute_cases.jsonl
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
REVIEWS = ROOT / "data" / "reviews" / "reviews.sqlite"
CASES = ROOT / "evals" / "attribute_cases.jsonl"

# Phrases a shopper would actually type, with how many queries to build per phrase.
ATTRIBUTES = [
    "runs small",
    "too tight",
    "leaks",
    "very noisy",
    "smells",
    "broke after",
    "battery dies",
    "too heavy",
    "flimsy",
    "stopped working",
    "poor quality",
    "hard to use",
]
PER_ATTRIBUTE = 3


def _load() -> tuple[list[dict], dict[str, list[tuple[str, str]]]]:
    from app.reviews.clean import clean_review, is_usable_body

    products = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else []
    reviews: dict[str, list[tuple[str, str]]] = {}
    if REVIEWS.exists():
        connection = sqlite3.connect(REVIEWS)
        for sku, title, text in connection.execute("SELECT product_id, title, text FROM reviews"):
            cleaned = clean_review(text, title)
            if is_usable_body(cleaned):
                reviews.setdefault(sku, []).append((cleaned, title))
    return products, reviews


def build(products: list[dict], reviews: dict[str, list[tuple[str, str]]]) -> list[dict]:
    """One query per (attribute, qualifying product), labelled by the review itself."""
    cases: list[dict] = []
    for attribute in ATTRIBUTES:
        found = 0
        for product in products:
            if found >= PER_ATTRIBUTE:
                break
            sku = str(product.get("sku") or "")
            product_type = (product.get("type") or "").strip()
            if not sku or not product_type:
                continue
            haystack = f"{product.get('title') or ''} {' '.join(product.get('tags') or [])}"
            # The phrase must be review-only: if it were in the title, a keyword
            # retriever would satisfy the query without any enrichment.
            if attribute in haystack.lower():
                continue
            evidence = [text for text, _ in reviews.get(sku, []) if attribute in text.lower()]
            if not evidence:
                continue
            found += 1
            cases.append(
                {
                    "case_id": f"attr-{attribute.replace(' ', '-')}-{found}",
                    "attribute": attribute,
                    # A realistic keyword query: the category plus the attribute the
                    # customer would type. The label is the review, not the phrasing.
                    "query": f"{product_type} {attribute}",
                    "expected_ids": [product["id"]],
                    "evidence": evidence[0][:160],
                }
            )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    products, reviews = _load()
    cases = build(products, reviews)
    by_attribute: dict[str, int] = {}
    for case in cases:
        by_attribute[case["attribute"]] = by_attribute.get(case["attribute"], 0) + 1
    print(f"products={len(products)} products_with_reviews={len(reviews)} cases={len(cases)}")
    print(f"by attribute: {by_attribute}")
    for case in cases[:3]:
        print(f"  {case['query']!r} -> {case['evidence'][:70]!r}")
    if args.write:
        CASES.write_text("\n".join(json.dumps(case) for case in cases) + "\n")
        print(f"wrote {CASES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
