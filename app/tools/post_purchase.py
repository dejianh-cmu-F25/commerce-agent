"""Post-purchase tools for the resolution agent (feature 045).

Reads are open; ``propose_return_decision`` records a **proposal** and has no side
effect. The harness (``app.returns.eligibility``) disposes: it verifies the
proposal against the order and the policy. Nothing here approves or refunds (P3).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.gates.base import GateContext
from app.gates.policy import PolicyGate
from app.ports.post_purchase import OrderView, PostPurchaseBackend
from app.returns.amazon_policy import ReturnFacts
from app.tools.registry import ToolRegistry, ToolResult

GET_ORDER_SPEC = ToolSpec(
    name="get_order_status",
    description=(
        "Get one order's status, dates, and line items by its id. Call this before "
        "answering anything about an order."
    ),
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order id."}},
        "required": ["order_id"],
    },
)

RETURNABLE_SPEC = ToolSpec(
    name="list_returnable_items",
    description=(
        "List the items on an order that can be returned, with their fulfillment "
        "line item ids. Call this before proposing a return."
    ),
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order id."}},
        "required": ["order_id"],
    },
)

PROPOSE_SPEC = ToolSpec(
    name="propose_return_decision",
    description=(
        "Propose a return decision for one item: eligible, ineligible, or escalate. "
        "Cite the policy clause ids that support it. This records a proposal only; "
        "it never approves or refunds."
    ),
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "fulfillment_line_item_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["eligible", "ineligible", "escalate"]},
            "reason": {
                "type": "string",
                "enum": [
                    "unwanted",
                    "size_too_small",
                    "size_too_large",
                    "damaged",
                    "defective",
                    "wrong_item",
                    "missing",
                ],
            },
            "cited_clauses": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["order_id", "fulfillment_line_item_id", "decision"],
    },
)

_DECISIONS = {"eligible", "ineligible", "escalate"}


def _category_from_tags(tags: tuple[str, ...]) -> str:
    """A product's policy category: an explicit ``category:<x>`` tag, else ``all``."""
    for tag in tags:
        if tag.startswith("category:"):
            return tag.split(":", 1)[1]
    return "all"


def _order_dict(order: OrderView) -> dict[str, Any]:
    return {
        "id": order.id,
        "name": order.name,
        "created_at": order.created_at,
        "financial_status": order.financial_status,
        "fulfillment_status": order.fulfillment_status,
        "delivered_at": order.delivered_at,
        "total": order.total,
        "currency": order.currency,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "quantity": item.quantity,
                "sku": item.sku,
                "tags": list(item.tags),
            }
            for item in order.line_items
        ],
    }


def register_post_purchase_tools(
    registry: ToolRegistry,
    backend: PostPurchaseBackend,
    *,
    policy_gate: PolicyGate | None = None,
) -> None:
    """Register the read tools and the (side-effect-free) proposal tool.

    When ``policy_gate`` is provided, every proposal is validated against the
    policy SoT at runtime (P3); a proposal that contradicts the policy is rejected
    with ``validated=false`` rather than silently recorded.
    """

    async def get_order_status(arguments: dict[str, Any], session: Session) -> ToolResult:
        order_id = str(arguments.get("order_id", ""))
        order = await backend.get_order(order_id)
        if order is None:
            return ToolResult(content=f"unknown order: {order_id}", status="error")
        session.remember_ids([order.id])
        return ToolResult(content=json.dumps(_order_dict(order)), component="order")

    async def list_returnable_items(arguments: dict[str, Any], session: Session) -> ToolResult:
        order_id = str(arguments.get("order_id", ""))
        items = await backend.returnable_items(order_id)
        payload = [
            {
                "fulfillment_line_item_id": item.fulfillment_line_item_id,
                "title": item.title,
                "sku": item.sku,
                "quantity": item.quantity,
            }
            for item in items
        ]
        return ToolResult(content=json.dumps(payload), component="returnable_items")

    async def propose_return_decision(arguments: dict[str, Any], session: Session) -> ToolResult:
        decision = str(arguments.get("decision", "")).strip().lower()
        if decision not in _DECISIONS:
            return ToolResult(
                content="decision must be one of eligible|ineligible|escalate", status="error"
            )
        order_id = str(arguments.get("order_id", ""))
        fli_id = str(arguments.get("fulfillment_line_item_id", ""))
        record = {
            "order_id": order_id,
            "fulfillment_line_item_id": fli_id,
            "decision": decision,
            "cited_clauses": [str(c) for c in arguments.get("cited_clauses", [])],
        }
        if policy_gate is not None:
            order = await backend.get_order(order_id)
            items = order.line_items if order else []
            item = next((line for line in items if line.id == fli_id), None) or (
                items[0] if items else None
            )
            tags = tuple(item.tags) if item else ()
            facts = ReturnFacts(
                order_id=order_id,
                fulfillment_line_item_id=fli_id,
                reason=str(arguments.get("reason", "unwanted")),
                delivered_at=order.delivered_at if order else None,
                category=_category_from_tags(tags),
                tags=tags,
            )
            verdict = policy_gate.check(
                GateContext(session=session, facts=facts, proposed=decision)
            )
            if not verdict.allowed:
                return ToolResult(
                    content=json.dumps({**record, "validated": False, "policy": verdict.reason}),
                    status="error",
                )
            record["validated"] = True
        return ToolResult(content=json.dumps(record), component="return_decision")

    registry.register(GET_ORDER_SPEC, get_order_status)
    registry.register(RETURNABLE_SPEC, list_returnable_items)
    registry.register(PROPOSE_SPEC, propose_return_decision)
