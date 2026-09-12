"""In-memory storefront provider (Service Provider for
:class:`app.ports.storefront.StorefrontBackend`).

Used for keyless runs and tests; seeded from the shared catalog. Orders are
seeded per customer on first access when ``seed_orders`` is set (feature 014).
"""

from __future__ import annotations

from app.adapters.order_seed import demo_orders
from app.adapters.storefront_common import clamp_limit, rank_products
from app.core.types import Order, Product


class InMemoryStorefront:
    def __init__(self, products: list[Product], seed_orders: bool = True) -> None:
        self._products = list(products)
        self._seed_orders = seed_orders
        self._orders: dict[str, list[Order]] = {}

    def search(self, query: str, limit: int) -> list[Product]:
        return rank_products(self._products, query)[: clamp_limit(limit)]

    def get(self, product_id: str) -> Product | None:
        return next((p for p in self._products if p.id == product_id), None)

    def list_orders(self, customer_id: str) -> list[Order]:
        if not customer_id:
            return []
        if customer_id not in self._orders and self._seed_orders:
            self._orders[customer_id] = demo_orders(customer_id)
        orders = self._orders.get(customer_id, [])
        return sorted(orders, key=lambda order: order.placed_at, reverse=True)

    def get_order(self, customer_id: str, order_id: str) -> Order | None:
        return next((o for o in self.list_orders(customer_id) if o.id == order_id), None)
