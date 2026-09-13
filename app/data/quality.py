"""Data quality at the boundaries (feature 027, RW-2).

Validate and normalize external data (catalog rows, order rows) before it enters
the domain. Dirty data has **defined behavior**: fixable values are normalized;
unusable rows are rejected (skipped in ``repair`` mode, raising in ``strict``).
No silent assumptions about upstream data.

Pure functions, stdlib only.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.core.types import Order, OrderItem, Product

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PRICE = re.compile(r"-?\d+(?:\.\d+)?")
_INT = re.compile(r"-?\d+")
_ORDER_STATUS = ("processing", "shipped", "delivered", "cancelled")


def clean_text(value: Any) -> str:
    """Trim, collapse whitespace, and strip control characters."""
    if value is None:
        return ""
    text = _CONTROL.sub(" ", str(value))
    return " ".join(text.split()).strip()


def parse_price(value: Any) -> float | None:
    """Parse a price from a number or a string like ``"$1,299.00"``.

    Returns ``None`` for missing, unparseable, or negative values.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2) if float(value) >= 0 else None
    match = _PRICE.search(str(value or "").replace(",", "").strip())
    if match is None:
        return None
    price = float(match.group())
    return round(price, 2) if price >= 0 else None


def parse_stock(value: Any) -> int | None:
    """Parse a stock level from a number or a string; ``None`` if unusable.

    ``"out of stock"`` and explicit negatives have defined results (0 / None).
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value) if value >= 0 else None
    text = str(value or "").strip().lower()
    if text in {"", "n/a", "unknown"}:
        return None
    if "out of stock" in text or text in {"no", "false"}:
        return 0
    match = _INT.search(text)
    if match is None:
        return None
    stock = int(match.group())
    return stock if stock >= 0 else None


def parse_tags(value: Any) -> list[str]:
    """Parse tags from a list or a comma-separated string; deduped, lowercased."""
    if value is None:
        return []
    raw = value if isinstance(value, (list, tuple)) else str(value).split(",")
    tags: list[str] = []
    for item in raw:
        tag = clean_text(item).lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def normalize_product(raw: Mapping[str, Any]) -> Product | None:
    """Return a clean :class:`Product`, or ``None`` if the row is unusable."""
    product_id = clean_text(raw.get("id"))
    title = clean_text(raw.get("title"))
    price = parse_price(raw.get("price"))
    stock = parse_stock(raw.get("stock"))
    if not product_id or not title or price is None or stock is None:
        return None
    return Product(
        id=product_id, title=title, price=price, stock=stock, tags=parse_tags(raw.get("tags"))
    )


def _normalize_status(value: Any) -> str | None:
    status = clean_text(value).lower()
    return status if status in _ORDER_STATUS else None


def normalize_order(
    customer_id: str, raw: Mapping[str, Any], items: Sequence[Mapping[str, Any]]
) -> Order | None:
    """Return a clean :class:`Order`, or ``None`` if the row is unusable.

    Invalid line items are dropped; an order with no valid items is invalid.
    """
    order_id = clean_text(raw.get("id"))
    status = _normalize_status(raw.get("status"))
    if not order_id or status is None:
        return None

    clean_items: list[OrderItem] = []
    for item in items:
        product_id = clean_text(item.get("product_id"))
        title = clean_text(item.get("title"))
        quantity = parse_stock(item.get("quantity"))
        unit_price = parse_price(item.get("unit_price"))
        if not product_id or not title or quantity is None or quantity < 1 or unit_price is None:
            continue
        clean_items.append(OrderItem(product_id, title, quantity, unit_price))
    if not clean_items:
        return None

    total = parse_price(raw.get("total"))
    if total is None:
        total = round(sum(item.line_total for item in clean_items), 2)

    return Order(
        id=order_id,
        customer_id=clean_text(customer_id),
        status=status,
        placed_at=clean_text(raw.get("placed_at")),
        delivered_at=clean_text(raw.get("delivered_at")) or None,
        total=total,
        items=clean_items,
    )
