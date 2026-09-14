"""Post-purchase capability: Service Definition (feature 045).

The system of record for orders and returns. **Reads are open; a return request
is a proposal** the harness gates and a human approves (P3). Providers: the
Shopify Admin API (real) and an in-memory fixture (keyless default).

Only server-issued ids may enter the session (grounding, P4); the ids here are
Shopify global ids (``gid://shopify/...``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LineItem:
    id: str
    title: str
    quantity: int
    sku: str = ""
    # Product tags (e.g. final_sale, large). Shopify exposes these on the product;
    # the fixture sets them directly.
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrderView:
    """A read-only view of an order, enough to ground a WISMO or return answer."""

    id: str
    name: str
    created_at: str
    financial_status: str
    fulfillment_status: str
    total: float
    currency: str
    delivered_at: str | None = None
    line_items: list[LineItem] = field(default_factory=list)


@dataclass(frozen=True)
class ReturnableItem:
    """One fulfillment line item that can be returned, with its quantity."""

    fulfillment_line_item_id: str
    title: str
    sku: str
    quantity: int


class PostPurchaseBackend(Protocol):
    async def get_order(self, order_id: str) -> OrderView | None:
        """Return the order with ``order_id``, or ``None``."""
        ...

    async def returnable_items(self, order_id: str) -> list[ReturnableItem]:
        """Return the fulfillment line items eligible to be returned.

        An order that is unfulfilled or unknown returns ``[]``.
        """
        ...
