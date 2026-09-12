"""In-memory storefront provider (Service Provider for
:class:`app.ports.storefront.StorefrontBackend`).

Used for keyless runs and tests; seeded from the shared catalog.
"""

from __future__ import annotations

from app.adapters.storefront_common import clamp_limit, rank_products
from app.core.types import Product


class InMemoryStorefront:
    def __init__(self, products: list[Product]) -> None:
        self._products = list(products)

    def search(self, query: str, limit: int) -> list[Product]:
        return rank_products(self._products, query)[: clamp_limit(limit)]

    def get(self, product_id: str) -> Product | None:
        return next((p for p in self._products if p.id == product_id), None)
