"""The MCP customer-accounts surface enforces the gates (046 hardening, WP-6).

The tools used to be registered without a policy gate on this surface, so the
runtime "model proposes, harness disposes" guarantee was absent. This pins the fix.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.core.session import Session
from app.core.settings import load_settings
from app.mcp.server import customer_accounts_registry
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem

ME = "gid://shopify/Customer/me"


def _backend(delivered_days_ago: int) -> InMemoryPostPurchase:
    delivered = (datetime.now(UTC) - timedelta(days=delivered_days_ago)).isoformat()
    order = OrderView(
        id="order-1",
        name="#1",
        created_at=delivered,
        financial_status="PAID",
        fulfillment_status="FULFILLED",
        total=50.0,
        currency="USD",
        delivered_at=delivered,
        line_items=[
            LineItem(id="fli-1", title="Tent", quantity=1, sku="SKU", tags=("category:all",))
        ],
        customer_id=ME,
    )
    return InMemoryPostPurchase(
        {"order-1": order}, {"order-1": [ReturnableItem("fli-1", "Tent", "SKU", 1)]}
    )


def _registry(days: int):
    return customer_accounts_registry(load_settings(), _backend(days))


async def test_mcp_rejects_a_proposal_that_contradicts_the_policy():
    # Delivered 400 days ago: the engine says ineligible; the model proposes eligible.
    registry = _registry(400)
    session = Session(id="mcp", customer_id=ME)
    result = await registry.execute(
        "propose_return_decision",
        {"order_id": "order-1", "item_ref": 1, "decision": "eligible", "reason": "unwanted"},
        session,
    )
    assert result.status == "error"
    body = json.loads(result.content)
    assert body["validated"] is False
    assert result.blocked_by == "policy"


async def test_mcp_allows_a_proposal_that_agrees_with_the_policy():
    registry = _registry(5)  # inside the window
    session = Session(id="mcp", customer_id=ME)
    result = await registry.execute(
        "propose_return_decision",
        {"order_id": "order-1", "item_ref": 1, "decision": "eligible", "reason": "unwanted"},
        session,
    )
    assert result.status == "ok"
    body = json.loads(result.content)
    assert body["validated"] is True
    assert body["cited_clauses"]
