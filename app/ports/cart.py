"""Cart capability: Service Definition (constitution PB-2, feature 046, T108).

A cart is a proposal (P3): adding to it changes nothing about money, and completing a
checkout is a separate, human-approved step. Providers live in ``app/adapters`` and are
selected by configuration (PB-1) - the session-backed one is the keyless default, and a
Storefront-backed one exists for deployments that want a real platform cart.
"""

from __future__ import annotations

from typing import Protocol

from app.core.session import CartLine, Session
from app.core.types import Product


class CartBackend(Protocol):
    def add(self, session: Session, product: Product, quantity: int) -> None:
        """Add ``quantity`` of ``product`` to the session's cart."""
        ...

    def view(self, session: Session) -> list[CartLine]:
        """Return the session's cart lines."""
        ...
