"""Labeled dirty inputs for the data-quality benchmark (feature 027, RW-2).

Each case pairs a normalizer with a raw value and its expected canonical result.
``None`` means "reject the value". Kept small and hand-curated; broader fuzzing is
out of scope (see the spec).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Case:
    kind: str
    raw: Any
    expected: Any


DATA_QUALITY_SET: list[Case] = [
    # clean_text
    Case("clean_text", "  Wireless\tHeadphones  ", "Wireless Headphones"),
    Case("clean_text", None, ""),
    Case("clean_text", "a\x00b", "a b"),
    # parse_price
    Case("parse_price", "$1,299.00", 1299.00),
    Case("parse_price", "  USD 45.5 ", 45.50),
    Case("parse_price", 19.999, 20.00),
    Case("parse_price", "", None),
    Case("parse_price", "-5", None),
    Case("parse_price", "free", None),
    # parse_stock
    Case("parse_stock", "12", 12),
    Case("parse_stock", "out of stock", 0),
    Case("parse_stock", 0, 0),
    Case("parse_stock", "", None),
    Case("parse_stock", -3, None),
    Case("parse_stock", "n/a", None),
    # parse_tags
    Case("parse_tags", "Audio, audio , NEW", ["audio", "new"]),
    Case("parse_tags", None, []),
    # normalize_product
    Case(
        "normalize_product",
        {
            "id": "P1",
            "title": "  Tent ",
            "price": "$120.00",
            "stock": "out of stock",
            "tags": "camping",
        },
        ("P1", "Tent", 120.0, 0, ["camping"]),
    ),
    Case("normalize_product", {"id": "", "title": "x", "price": 1.0, "stock": 1}, None),
    Case("normalize_product", {"id": "P2", "title": "y", "price": "free", "stock": 1}, None),
]
