"""ACP checkout adapter and tools (feature 046)."""

from __future__ import annotations

import asyncio
import json

from app.adapters.acp_checkout import AcpCheckout
from app.core.session import Session
from app.ports.checkout import COMPLETED, CREATED, FAILED, READY
from app.tools.checkout import register_checkout_tools
from app.tools.registry import ToolRegistry


def test_lifecycle() -> None:
    checkout = AcpCheckout()
    session = checkout.create_session("cart_1", 42.0)
    assert session.status == CREATED
    assert checkout.update_session(session.id, "1 Main St").status == READY
    done = checkout.complete(session.id)
    assert done.status == COMPLETED
    assert done.charge_issued is False
    assert done.payment_token


def test_premature_complete_fails() -> None:
    checkout = AcpCheckout()
    session = checkout.create_session("cart_1", 42.0)
    assert checkout.complete(session.id).status == FAILED


def test_unknown_session_raises() -> None:
    try:
        AcpCheckout().complete("nope")
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_checkout_tools(registry, AcpCheckout())
    return registry


def test_complete_requires_human_approval() -> None:
    registry = _registry()
    session = Session(id="t")
    created = asyncio.run(
        registry.execute("create_checkout_session", {"cart_id": "c1", "total": 5}, session)
    )
    session_id = json.loads(created.content)["id"]
    asyncio.run(
        registry.execute("update_checkout", {"session_id": session_id, "address": "x"}, session)
    )

    pending = asyncio.run(
        registry.execute("complete_checkout", {"session_id": session_id}, session)
    )
    assert pending.status == "error"
    assert json.loads(pending.content)["status"] == "pending_approval"

    done = asyncio.run(
        registry.execute("complete_checkout", {"session_id": session_id, "approved": True}, session)
    )
    payload = json.loads(done.content)
    assert payload["status"] == COMPLETED
    assert payload["charge_issued"] is False
