"""Shared helpers for storefront providers (limit clamping and ranking).

Keeping ranking here means every provider returns the same order for the same
query (parity, SC-001).
"""

from __future__ import annotations

from app.core.types import Product

MIN_LIMIT = 1
MAX_LIMIT = 50


def clamp_limit(limit: int) -> int:
    return max(MIN_LIMIT, min(MAX_LIMIT, limit))


def rank_products(products: list[Product], query: str) -> list[Product]:
    """Rank by keyword overlap on title + tags; ties by lower price.

    An empty query yields no results (never the whole catalog).
    """
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []
    scored: list[tuple[int, Product]] = []
    for item in products:
        haystack = f"{item.title} {' '.join(item.tags)}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].price))
    return [item for _, item in scored]
