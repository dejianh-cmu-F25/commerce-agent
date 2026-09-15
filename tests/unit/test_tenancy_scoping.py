"""INV-7: an order that declares another owner is refused before it is read.

The gate existed but read a field `OrderView` did not have, and no tool used it, so
cross-customer reads were unenforced. These pin the three cases that matter.
"""

from __future__ import annotations

import asyncio
import json

from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.core.session import Session
from app.gates.tenancy import TenancyGate
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem
from app.tools.post_purchase import register_post_purchase_tools
from app.tools.registry import ToolRegistry

ME = "gid://shopify/Customer/1"
SOMEONE_ELSE = "gid://shopify/Customer/2"


def _registry(owner: str) -> ToolRegistry:
    order = OrderView(
        id="1006",
        name="#1006",
        created_at="2026-02-20T00:00:00+00:00",
        financial_status="PAID",
        fulfillment_status="FULFILLED",
        total=34.99,
        currency="USD",
        delivered_at="2026-02-25T00:00:00+00:00",
        line_items=[LineItem(id="fli-1", title="Sonic Rush Adventure", quantity=1, sku="B0")],
        customer_id=owner,
    )
    backend = InMemoryPostPurchase(
        {"1006": order}, {"1006": [ReturnableItem("fli-1", "Sonic Rush Adventure", "B0", 1)]}
    )
    registry = ToolRegistry()
    register_post_purchase_tools(registry, backend, tenancy_gate=TenancyGate())
    return registry


def _call(owner: str, tool: str, arguments: dict, customer: str = ME) -> tuple[dict, str]:
    registry = _registry(owner)
    session = Session(id="t", customer_id=customer)
    result = asyncio.run(registry.execute(tool, arguments, session))
    return json.loads(result.content), result.status


def test_another_customers_order_is_refused_without_leaking_it():
    """The refusal names no line item, no total, no delivery date."""
    payload, status = _call(SOMEONE_ELSE, "get_order_status", {"order_id": "1006"})
    assert payload["accessible"] is False
    assert "another customer" in payload["reason"]
    assert "Sonic Rush" not in json.dumps(payload)
    # A refusal is not a system error: the model should relay it, not retry it.
    assert status == "ok"


def test_the_same_refusal_applies_to_every_order_reading_tool():
    for tool, arguments in (
        ("list_returnable_items", {"order_id": "1006"}),
        (
            "propose_return_decision",
            {"order_id": "1006", "item_ref": 1, "decision": "eligible", "reason": "unwanted"},
        ),
    ):
        payload, status = _call(SOMEONE_ELSE, tool, arguments)
        assert payload["accessible"] is False, tool
        assert status == "ok", tool


def test_your_own_order_is_readable():
    payload, _ = _call(ME, "get_order_status", {"order_id": "1006"})
    assert payload["name"] == "#1006"


def test_an_order_with_no_declared_owner_is_readable():
    """Keyless fixtures declare no owner; there is nothing to protect, so nothing breaks."""
    payload, _ = _call("", "get_order_status", {"order_id": "1006"})
    assert payload["name"] == "#1006"


def test_an_authenticated_customer_is_required_for_an_owned_order():
    """The safe direction: an owned order plus no principal is refused, not trusted."""
    payload, _ = _call(SOMEONE_ELSE, "get_order_status", {"order_id": "1006"}, customer="")
    assert payload["accessible"] is False
