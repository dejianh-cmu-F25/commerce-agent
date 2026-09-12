"""Return eligibility policy (feature 014).

A pure, deterministic function of the order and the configured window. No model
decides eligibility (computational control, HR-4); the tool renders the decision
and its reason.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.types import Order

RETURNABLE_STATUS = "delivered"


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def return_eligibility(
    order: Order, product_id: str, window_days: int, now: datetime | None = None
) -> tuple[bool, str]:
    """Return ``(eligible, reason)`` for returning ``product_id`` on ``order``."""
    now = now or datetime.now(UTC)
    item = next((line for line in order.items if line.product_id == product_id), None)
    if item is None:
        return False, f"{product_id} is not on order {order.id}"
    if order.status != RETURNABLE_STATUS:
        return False, f"order {order.id} is {order.status}, not delivered"
    delivered = _parse(order.delivered_at)
    if delivered is None:
        return False, f"order {order.id} has no delivery date"
    age_days = max(0, (now - delivered).days)
    if age_days > window_days:
        return False, (
            f"order {order.id} was delivered {age_days} days ago; "
            f"the return window is {window_days} days"
        )
    return True, f"within the {window_days}-day return window"
