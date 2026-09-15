"""Post-purchase tools for the resolution agent (feature 045).

Reads are open; ``propose_return_decision`` records a **proposal** and has no side
effect. The harness (``app.returns.eligibility``) disposes: it verifies the
proposal against the order and the policy. Nothing here approves or refunds (P3).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
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
        "Get one order's status, dates, line items and the items that can be "
        "returned, by its id. Call this once before answering anything about an "
        "order or proposing a return."
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
        "List the items on an order that can be returned. get_order_status already "
        "includes these, so only call this if you need them separately."
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
        "Do not supply clause ids — the harness attaches the clauses it used. This "
        "records a proposal only; it never approves or refunds."
    ),
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "item_ref": {
                "type": "integer",
                "description": (
                    "The item's ref from get_order_status (1 for the first item). "
                    "Prefer this over copying a long fulfillment_line_item_id."
                ),
            },
            "fulfillment_line_item_id": {
                "type": "string",
                "description": "The full item id, if you already have it.",
            },
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
            "cited_clauses": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional; the harness fills this in. Do not guess it.",
            },
        },
        "required": ["order_id", "decision"],
    },
)

_DECISIONS = {"eligible", "ineligible", "escalate"}


def _category_from_tags(tags: tuple[str, ...]) -> str:
    """A product's policy category: an explicit ``category:<x>`` tag, else ``all``."""
    for tag in tags:
        if tag.startswith("category:"):
            return tag.split(":", 1)[1]
    return "all"


def _order_dict(order: OrderView, returnable: Sequence[Any] = ()) -> dict[str, Any]:
    """One order payload that already answers "what can be returned".

    Folding the returnable items in removes a second round trip and the id
    confusion it caused: the model used to re-call list_returnable_items with the
    internal id it had just read instead of the customer-facing one.
    """
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
        "returnable_items": [
            {
                "ref": index,
                "title": item.title,
                "sku": item.sku,
                "quantity": item.quantity,
                "fulfillment_line_item_id": item.fulfillment_line_item_id,
            }
            for index, item in enumerate(returnable, 1)
        ],
    }


def register_post_purchase_tools(
    registry: ToolRegistry,
    backend: PostPurchaseBackend,
    *,
    policy_gate: PolicyGate | None = None,
    now: datetime | None = None,
) -> None:
    """Register the read tools and the (side-effect-free) proposal tool.

    When ``policy_gate`` is provided, every proposal is validated against the
    policy SoT at runtime (P3); a proposal that contradicts the policy is rejected
    with ``validated=false`` rather than silently recorded. ``now`` pins the clock
    for deterministic evaluations; production leaves it ``None`` (wall clock).
    """

    async def get_order_status(arguments: dict[str, Any], session: Session) -> ToolResult:
        order_id = str(arguments.get("order_id", ""))
        order = await backend.get_order(order_id)
        if order is None:
            return ToolResult(content=f"unknown order: {order_id}", status="error")
        session.remember_ids([order.id])
        # order.id is the resolved global id: never pass the customer-facing number
        # to a backend that expects a global id.
        returnable = await backend.returnable_items(order.id)
        return ToolResult(content=json.dumps(_order_dict(order, returnable)), component="order")

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
        # Resolve the item by its short ref when possible: asking the model to copy
        # an opaque gid is what made it loop.
        returnable = await backend.returnable_items(order_id)
        ref = arguments.get("item_ref")
        if ref is not None:
            try:
                index = int(ref)
            except (TypeError, ValueError):
                index = 0
            if not 1 <= index <= len(returnable):
                return ToolResult(
                    content=json.dumps(
                        {
                            "error": "item_ref out of range",
                            "valid_refs": list(range(1, len(returnable) + 1)),
                        }
                    ),
                    status="error",
                )
            fli_id = returnable[index - 1].fulfillment_line_item_id
        valid_ids = [item.fulfillment_line_item_id for item in returnable]
        if returnable and fli_id not in valid_ids:
            return ToolResult(
                content=json.dumps(
                    {
                        "error": "unknown item; pass item_ref instead",
                        "valid_refs": list(range(1, len(returnable) + 1)),
                        "items": [item.title for item in returnable],
                    }
                ),
                status="error",
            )
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
                GateContext(session=session, facts=facts, proposed=decision, now=now)
            )
            # The gate re-derives the decision from the policy SoT; its clause ids are
            # authoritative, so the proposal cites the harness's clauses, not the
            # model's recollection (model proposes, harness disposes).
            if verdict.cited_clauses:
                record["cited_clauses"] = list(verdict.cited_clauses)
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
