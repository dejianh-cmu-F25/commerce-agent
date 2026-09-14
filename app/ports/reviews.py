"""Product reviews capability: Service Definition (constitution PB-2, feature 046).

Real customer reviews from Amazon Reviews'23, stored locally (Shopify has no native
review object). The model reads reviews to answer "what do customers say"; it never
invents one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Review:
    product_id: str  # the parent ASIN (our SKU)
    rating: float
    title: str
    text: str
    helpful_votes: int = 0
    verified: bool = False
    timestamp_ms: int = 0


class ReviewBackend(Protocol):
    def get_reviews(self, product_id: str, limit: int = 5) -> list[Review]:
        """Return up to ``limit`` reviews for a product, most helpful first."""
        ...
