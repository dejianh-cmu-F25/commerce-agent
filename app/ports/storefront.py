"""Storefront capability: Service Definition (constitution PB-2).

The catalog is the source of truth for prices and stock. Only ids returned by
this port may enter the session (grounding, P4). Providers live in
``app/adapters`` and are selected by configuration (PB-1).
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Order, Product


class StorefrontBackend(Protocol):
    def search(self, query: str, limit: int) -> list[Product]:
        """Return at most ``limit`` products matching ``query``.

        An empty query returns ``[]``; the caller never receives the whole
        catalog by accident.
        """
        ...

    def get(self, product_id: str) -> Product | None:
        """Return the product with ``product_id``, or ``None``."""
        ...

    def list_orders(self, customer_id: str) -> list[Order]:
        """Return the customer's orders, newest first.

        An empty ``customer_id`` returns ``[]``. Demo orders are seeded
        idempotently when configured (feature 014).
        """
        ...

    def get_order(self, customer_id: str, order_id: str) -> Order | None:
        """Return one of the customer's orders, or ``None``."""
        ...
