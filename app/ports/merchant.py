"""Merchant capability: Service Definition (constitution P3, PB-2).

The operator face. The model may **propose** changes; only a human approves them
(``apply``). Providers live in ``app/adapters``.
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Change, Product


class MerchantBackend(Protocol):
    def list_products(self, limit: int = 100) -> list[Product]:
        """Return the catalog with prices and stock."""
        ...

    def stage_change(self, product_id: str, kind: str, new_value: float) -> Change:
        """Record a pending change. MUST NOT modify the product (P3).

        Raises ``ValueError`` for an unknown product or an invalid value.
        """
        ...

    def pending(self) -> list[Change]:
        """Return the staged changes awaiting approval."""
        ...

    def apply(self, change_id: str) -> Change | None:
        """Apply a pending change and mark it applied.

        Returns ``None`` if the change is unknown or already applied (no
        double-apply, RD-2).
        """
        ...
