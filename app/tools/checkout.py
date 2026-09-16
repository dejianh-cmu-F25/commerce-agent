"""Checkout tools (feature 046).

``complete_checkout`` is **HITL-gated**: without an explicit human approval it
returns a pending-approval result and does not complete. The adapter never
charges; the project takes no money (P3).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.checkout import CheckoutBackend
from app.tools.registry import ToolRegistry, ToolResult

CREATE_SPEC = ToolSpec(
    name="create_checkout_session",
    description=(
        "Open a checkout session for a cart. Returns a session id and the total. "
        "This does not take payment."
    ),
    parameters={
        "type": "object",
        "properties": {
            "cart_id": {"type": "string"},
            "total": {"type": "number"},
            "currency": {"type": "string"},
        },
        "required": ["cart_id", "total"],
    },
)

UPDATE_SPEC = ToolSpec(
    name="update_checkout",
    description="Attach the buyer's delivery address to a checkout session.",
    parameters={
        "type": "object",
        "properties": {"session_id": {"type": "string"}, "address": {"type": "string"}},
        "required": ["session_id", "address"],
    },
)

COMPLETE_SPEC = ToolSpec(
    name="complete_checkout",
    description=(
        "Complete a checkout session. Requires human approval: without approved=true "
        "it records a pending request and does not complete. No real payment is taken."
    ),
    parameters={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "approved": {"type": "boolean", "description": "Set true only after a human approves."},
        },
        "required": ["session_id"],
    },
)


def _session_dict(session: Any) -> dict[str, Any]:
    return {
        "id": session.id,
        "cart_id": session.cart_id,
        "status": session.status,
        "total": session.total,
        "currency": session.currency,
        "address": session.address,
        "payment_token": session.payment_token,
        "charge_issued": session.charge_issued,
    }


def register_checkout_tools(registry: ToolRegistry, checkout: CheckoutBackend) -> None:
    async def create_checkout_session(arguments: dict[str, Any], _session: Session) -> ToolResult:
        cart_id = str(arguments.get("cart_id", "")).strip()
        if not cart_id:
            return ToolResult(content="cart_id is required", status="error")
        session = checkout.create_session(
            cart_id, float(arguments.get("total", 0.0)), str(arguments.get("currency", "USD"))
        )
        payload = _session_dict(session)
        return ToolResult(content=json.dumps(payload), component="checkout", payload=payload)

    async def update_checkout(arguments: dict[str, Any], _session: Session) -> ToolResult:
        session_id = str(arguments.get("session_id", "")).strip()
        address = str(arguments.get("address", "")).strip()
        if not session_id or not address:
            return ToolResult(content="session_id and address are required", status="error")
        try:
            session = checkout.update_session(session_id, address)
        except KeyError as exc:
            return ToolResult(content=str(exc), status="error")
        payload = _session_dict(session)
        return ToolResult(content=json.dumps(payload), component="checkout", payload=payload)

    async def complete_checkout(arguments: dict[str, Any], _session: Session) -> ToolResult:
        session_id = str(arguments.get("session_id", "")).strip()
        try:
            session = checkout.complete(session_id)
        except KeyError as exc:
            return ToolResult(content=str(exc), status="error")
        payload = _session_dict(session)
        return ToolResult(content=json.dumps(payload), component="checkout", payload=payload)

    registry.register(CREATE_SPEC, create_checkout_session, effect="write")
    registry.register(UPDATE_SPEC, update_checkout, effect="write")
    # HITL is enforced by the ApprovalGate in the registry's gate set (046 hardening).
    registry.register(COMPLETE_SPEC, complete_checkout, effect="irreversible")
