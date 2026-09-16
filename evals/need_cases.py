#!/usr/bin/env python3
"""Need-based discovery queries with labels provable from the corpus (feature 047).

A **need query** names a task or situation, not a product ("something to keep dog
hair off my clothes while grooming him"), which is the query class a keyword index
cannot serve: the words that match live in the **review or feature text**, not in
the title. Each case's label is therefore provable, not judgement: the product is a
true positive because its own text states it serves the need, and the builder checks
that.

This is the need-query sibling of ``evals/attribute_cases.py`` (whose label is the
review phrase). The difference is scope: attribute cases measure one phrase
("runs small"); need cases measure a situated request that spans product text.

Run::

    uv run python evals/need_cases.py            # report what it found
    uv run python evals/need_cases.py --write    # write evals/need_cases.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
REVIEWS = ROOT / "data" / "reviews" / "reviews.sqlite"
CASES = ROOT / "evals" / "need_cases.jsonl"

# (query, title substring that uniquely identifies the product, evidence cue, need_type).
# The query is phrased as a need (its content words are deliberately NOT the title's),
# so a title-only index cannot satisfy it - the point of the measurement.
NEEDS: list[tuple[str, str, str, str]] = [
    (
        "I want to mix my own room freshener with essential oils",
        "MoYo Natural Labs",
        "room sprays",
        "task",
    ),
    (
        "something to keep dog hair off my clothes while grooming him",
        "Hairdresser Grooming Smock",
        "grooming my dogs",
        "task",
    ),
    (
        "something to keep my ears warm without a full hat",
        "New Balance Unisex Grid Fleece Headband",
        "full hat",
        "task",
    ),
    (
        "a gentle way to remove facial hair at home",
        "Sharonelle Natural Cream Soft Wax",
        "areas on the face",
        "task",
    ),
    (
        "an oil for a relaxing foot massage",
        "Clear Essence Specialist Skin Care Body Oil",
        "for massage",
        "task",
    ),
    ("a small beauty gift to give at a party", "Makeup Sponge Set", "gift giving", "gift"),
    ("hand soap for when there is no sink or water", "YouClean", "for travel", "task"),
    ("a face wash small enough to pack in a carry-on", "Osea Ocean Cleanser", "for travel", "task"),
    ("something to protect my braids while I sleep", "Satin Bonnet", "keep my braids", "task"),
    ("a brush to help me get 360 waves", "Wave Brush", "360 waves", "task"),
    ("a silly headband for a costume party", "Crab Headband", "festival", "gift"),
    (
        "something to get grease off my hands after working on the car",
        "GOJO Supro Max Cherry Hand Cleaner",
        "gets on your hands",
        "task",
    ),
    (
        "a case to keep my cosmetics safe when I travel",
        "Vaultz Locking Makeup Artist Case",
        "traveling",
        "task",
    ),
    (
        "something to keep my legs warm on a cold run",
        "RONNOX Women's 3-Pairs",
        "keep me warm",
        "task",
    ),
    ("a romantic present for my wife", "Allmygold Long Stem Dipped", "gift for my wife", "gift"),
    (
        "a lightweight layer for cool evenings outdoors",
        "ALPHA CAMP Men's Long-Sleeve Hooded",
        "camping or hiking",
        "task",
    ),
    (
        "something warm to sit around the campfire in",
        "Goodthreads Women's Heritage Fleece Basic Jogger",
        "campfire",
        "task",
    ),
    (
        "a cloth face covering I can throw in the laundry",
        "CELESTIAL SILK Face Mask Reusable",
        "easy to clean",
        "task",
    ),
    (
        "sun protection that will not look chalky on my skin",
        "Babo Botanicals Sheer Zinc",
        "no white residue",
        "attribute",
    ),
    (
        "products to keep dyed hair healthy in summer",
        "Joico Defy Damage Protective Set",
        "summer care",
        "task",
    ),
    (
        "something to dry laundry when I have no laundry room",
        "Xiaqing Clothes Dryer Portable",
        "first apartment",
        "task",
    ),
    (
        "replacement rollers for a dishwasher rack",
        "WPW10195417 UPGRADED 4 Packs Dishwasher Wheels",
        "wheel assembly",
        "task",
    ),
    (
        "a water flosser I can pack for a trip",
        "Waterpik Ultra Water Flosser",
        "convenient for travel",
        "task",
    ),
    (
        "hair ties that will not pull my daughter's hair",
        "Satin Bridesmaid Scrunchies",
        "high ponytails",
        "task",
    ),
]

_STOP = frozenset(
    "a an the my i to for of and or in on at with without me it is be that this "
    "something some when while after before what who want need can will not no".split()
)
_SENT = re.compile(r"(?<=[.!?])\s+")


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.casefold()) if w not in _STOP and len(w) > 2}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text or "") if s.strip()]


def _load() -> tuple[list[dict], dict[str, list[tuple[str, str]]]]:
    from app.reviews.clean import clean_review, is_usable_body

    products = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else []
    reviews: dict[str, list[tuple[str, str]]] = {}
    if REVIEWS.exists():
        connection = sqlite3.connect(REVIEWS)
        for sku, title, text in connection.execute("SELECT product_id, title, text FROM reviews"):
            cleaned = clean_review(text, title)
            if is_usable_body(cleaned):
                reviews.setdefault(str(sku), []).append((str(title or ""), cleaned))
        connection.close()
    return products, reviews


def build() -> list[dict]:
    products, reviews = _load()
    cases: list[dict] = []
    problems: list[str] = []
    for index, (query, title_sub, cue, need_type) in enumerate(NEEDS, 1):
        matches = [
            p for p in products if title_sub.casefold() in str(p.get("title", "")).casefold()
        ]
        if len(matches) != 1:
            problems.append(f"{query!r}: title substring matched {len(matches)} products")
            continue
        product = matches[0]
        evidence = ""
        for _title, body in reviews.get(str(product.get("sku") or ""), []):
            sentence = next((s for s in _sentences(body) if cue.casefold() in s.casefold()), "")
            if sentence:
                evidence = sentence
                break
        if not evidence:
            # Fall back to the feature/description text if the cue is there.
            if cue.casefold() in str(product.get("description", "")).casefold():
                evidence = next(
                    (
                        s
                        for s in _sentences(str(product["description"]))
                        if cue.casefold() in s.casefold()
                    ),
                    str(product.get("description", ""))[:200],
                )
        if not evidence:
            problems.append(f"{query!r}: cue {cue!r} not found in product text")
            continue
        overlap = sorted(_content_words(query) & _content_words(str(product.get("title", ""))))
        cases.append(
            {
                "case_id": f"need-{index:03d}",
                "need_type": need_type,
                "query": query,
                "language": "en",
                "expected_ids": [product["id"]],
                "evidence": evidence,
                "title_overlap_words": overlap,
                "notes": f"label provable: product text states it serves the need ({cue!r})",
            }
        )
    if problems:
        raise SystemExit("FAIL:\n  " + "\n  ".join(problems))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    cases = build()
    overlap = sum(1 for c in cases if not c["title_overlap_words"])
    by_type: dict[str, int] = {}
    for case in cases:
        by_type[case["need_type"]] = by_type.get(case["need_type"], 0) + 1
    print(f"{len(cases)} need cases; {overlap} with zero title overlap (pure need queries)")
    print("by type:", dict(sorted(by_type.items())))
    for case in cases:
        print(f"  [{case['need_type']:9}] {case['query'][:58]:58} -> {case['evidence'][:54]}")
    if args.write:
        CASES.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases))
        print(f"wrote {CASES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
