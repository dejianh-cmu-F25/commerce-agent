"""Post-purchase fixtures for the keyless scenario runner (feature 046).

The gold scenarios used to drive the legacy order tools (`list_orders`,
`start_return`) while production ran the closed-loop surface - so the gate was
validating a shelf nobody ships. They now drive the shipped tools, which need orders
the policy engine can actually decide on: one inside the return window, one outside
it. The clock is pinned so the window arithmetic is deterministic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem

FIXED_NOW = datetime(2026, 3, 1, tzinfo=UTC)
WINDOW_DAYS = 30


def _order(order_id: str, name: str, title: str, sku: str, *, delivered_days_ago: int) -> OrderView:
    line_id = f"FLI-{order_id}"
    return OrderView(
        id=order_id,
        name=name,
        created_at=(FIXED_NOW - timedelta(days=delivered_days_ago + 5)).isoformat(),
        financial_status="PAID",
        fulfillment_status="FULFILLED",
        total=189.0,
        currency="USD",
        delivered_at=(FIXED_NOW - timedelta(days=delivered_days_ago)).isoformat(),
        line_items=[LineItem(id=line_id, title=title, quantity=1, sku=sku)],
    )


def post_purchase_fixture() -> InMemoryPostPurchase:
    """Two orders: O-1001 within the window, O-1002 well outside it."""
    orders = {
        "O-1001": _order("O-1001", "#1001", "2-Person Tent", "TENT-2P", delivered_days_ago=5),
        "O-1002": _order("O-1002", "#1002", "Trail Backpack", "BAG-40L", delivered_days_ago=45),
    }
    return InMemoryPostPurchase(
        orders,
        {
            order_id: [
                ReturnableItem(
                    fulfillment_line_item_id=order.line_items[0].id,
                    title=order.line_items[0].title,
                    sku=order.line_items[0].sku,
                    quantity=1,
                )
            ]
            for order_id, order in orders.items()
        },
    )
