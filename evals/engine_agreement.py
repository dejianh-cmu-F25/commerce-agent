#!/usr/bin/env python3
"""Dual-run the legacy (014) and SoT (046) return engines; report agreement.

P0 migration step 1: the new engine must agree with the legacy engine on the
**shared decision surface** — a delivered, returnable item with a non-exception
reason. Divergences outside that surface are intentional (the new engine is
stricter) and are listed separately, never hidden.

Exit non-zero if the shared-surface agreement is below 1.0.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from app.core.types import Order, OrderItem
from app.returns.amazon_policy import (
    ELIGIBLE,
    ReturnFacts,
    decide_return,
    load_amazon_policy,
)
from app.returns.policy import return_eligibility

NOW = datetime(2026, 9, 15, tzinfo=UTC)
WINDOW_DAYS = 30
POLICY = load_amazon_policy()


def _delivered_at(days_ago: int | None) -> str | None:
    if days_ago is None:
        return None
    return (NOW - timedelta(days=days_ago)).isoformat()


def _order(days_ago: int | None, status: str = "delivered") -> Order:
    return Order(
        id="o1",
        customer_id="c1",
        status=status,
        placed_at=(NOW - timedelta(days=(days_ago or 0) + 3)).isoformat(),
        total=10.0,
        delivered_at=_delivered_at(days_ago),
        items=[OrderItem(product_id="p1", title="Thing", quantity=1, unit_price=10.0)],
    )


def _facts(days_ago: int | None, reason: str, category: str = "all") -> ReturnFacts:
    return ReturnFacts(
        order_id="o1",
        fulfillment_line_item_id="f1",
        reason=reason,
        delivered_at=_delivered_at(days_ago),
        category=category,
    )


def _legacy(days_ago: int | None, reason: str, status: str = "delivered") -> bool:
    allowed, _ = return_eligibility(_order(days_ago, status), "p1", WINDOW_DAYS, now=NOW)
    return allowed


def _new(days_ago: int | None, reason: str, category: str = "all") -> bool:
    return decide_return(_facts(days_ago, reason, category), POLICY, now=NOW).decision == ELIGIBLE


# The shared surface: delivered, returnable category, non-exception reason.
SHARED: list[tuple[int | None, str, str]] = [
    (9, "unwanted", "delivered"),
    (29, "unwanted", "delivered"),
    (30, "unwanted", "delivered"),  # boundary: exactly at the window is eligible
    (31, "unwanted", "delivered"),
    (60, "size_too_small", "delivered"),
    (None, "unwanted", "delivered"),  # no delivery date -> not eligible (both)
    (5, "unwanted", "shipped"),  # not delivered -> not eligible (both)
]

# Intentional divergences: the new engine is stricter (non-returnable, categories).
DIVERGENT: list[tuple[str, int, str, str]] = [
    ("non-returnable category", 5, "unwanted", "perishable"),
    ("short category window", 20, "unwanted", "digital_book"),  # 7-day window
    ("long category window", 45, "unwanted", "renewed_premium"),  # 365-day window
    ("exception outside window", 90, "damaged", "all"),
]


def main() -> int:
    agree = 0
    for days, reason, status in SHARED:
        legacy = _legacy(days, reason, status)
        # The fact is "delivered_at" — a non-delivered order has none.
        fact_days = days if status == "delivered" else None
        new = _new(fact_days, reason)
        if legacy == new:
            agree += 1
        else:
            print(f"  MISMATCH days={days} status={status}: legacy={legacy} new={new}")
    total = len(SHARED)
    rate = agree / total if total else 0.0
    print(f"shared-surface agreement: {agree}/{total} = {rate:.3f}")

    print("intentional divergences (new engine is stricter):")
    for label, days, reason, category in DIVERGENT:
        legacy = _legacy(days, reason)
        new = _new(days, reason, category)
        if legacy and not new:
            flag = "stricter"
        elif new and not legacy:
            flag = "looser"
        else:
            flag = "same"
        print(f"  {label}: legacy={legacy} new={new} ({flag})")

    if rate < 1.0:
        print(f"FAIL: shared-surface agreement {rate:.3f} < 1.000")
        return 1
    print("OK: shared-surface agreement = 1.000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
