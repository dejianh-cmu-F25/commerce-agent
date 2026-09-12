"""Seed products shared by the storefront adapters.

A single source for the demo catalog so the in-memory and SQLite providers stay
consistent (and so keyless runs still have data, P8).
"""

from __future__ import annotations

from app.core.types import Product

SEED_PRODUCTS: list[Product] = [
    Product(id="P-101", title="2-Person Tent", price=189.0, stock=12, tags=["camping", "tent"]),
    Product(id="P-102", title="Down Sleeping Bag", price=129.0, stock=7, tags=["camping", "sleep"]),
    Product(id="P-103", title="Camp Stove", price=64.0, stock=0, tags=["camping", "cook"]),
    Product(id="P-104", title="Trail Backpack 40L", price=95.0, stock=20, tags=["camping", "hike"]),
    Product(
        id="P-105",
        title="Insulated Water Bottle",
        price=24.0,
        stock=50,
        tags=["camping", "drink"],
    ),
]
