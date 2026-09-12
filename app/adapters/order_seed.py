"""Demo orders for the keyless storefront (feature 014).

The demo has no order placement (checkout is render-only, P3), so orders are
fixture data. Seeding is idempotent and per-customer, giving any browser's
customer id a small, deterministic history that exercises each status:

- ``O-1001`` delivered inside the return window (returnable)
- ``O-1002`` delivered outside the window (not returnable)
- ``O-1003`` shipped, not delivered (not returnable yet)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.types import Order, OrderItem


def demo_orders(customer_id: str, now: datetime | None = None) -> list[Order]:
    now = now or datetime.now(UTC)

    def days_ago(days: int) -> str:
        return (now - timedelta(days=days)).isoformat()

    return [
        Order(
            id="O-1001",
            customer_id=customer_id,
            status="delivered",
            placed_at=days_ago(14),
            delivered_at=days_ago(10),
            total=189.0,
            items=[OrderItem("P-101", "2-Person Tent", 1, 189.0)],
        ),
        Order(
            id="O-1002",
            customer_id=customer_id,
            status="delivered",
            placed_at=days_ago(50),
            delivered_at=days_ago(45),
            total=95.0,
            items=[OrderItem("P-104", "Trail Backpack 40L", 1, 95.0)],
        ),
        Order(
            id="O-1003",
            customer_id=customer_id,
            status="shipped",
            placed_at=days_ago(3),
            delivered_at=None,
            total=24.0,
            items=[OrderItem("P-105", "Insulated Water Bottle", 1, 24.0)],
        ),
    ]
