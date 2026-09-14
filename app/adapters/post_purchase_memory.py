"""In-memory post-purchase backend (feature 045, keyless default).

Serves the same contract as the Shopify adapter from fixtures, so the agent and
its evals run without a token (P8). Fixtures live in ``evals/fixtures/``.
"""

from __future__ import annotations

from app.ports.post_purchase import OrderView, ReturnableItem


class InMemoryPostPurchase:
    def __init__(
        self,
        orders: dict[str, OrderView],
        returnable: dict[str, list[ReturnableItem]] | None = None,
    ) -> None:
        self._orders = dict(orders)
        self._returnable = dict(returnable or {})

    async def get_order(self, order_id: str) -> OrderView | None:
        return self._orders.get(order_id)

    async def returnable_items(self, order_id: str) -> list[ReturnableItem]:
        return list(self._returnable.get(order_id, []))
