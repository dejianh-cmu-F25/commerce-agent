"""Post-purchase tools for the resolution agent (feature 045).

Reads are open; ``propose_return_decision`` records a **proposal** and has no side
effect. The harness (the ``PolicyGate``/``TenancyGate`` in the registry's gate
set) disposes: it verifies the proposal against the order and the policy. Nothing
here approves or refunds (P3).

Gates run at the registry choke point (046 hardening). Each order-reading tool
provides a ``context`` builder that resolves the order (for the tenancy gate) and,
for the proposal, the facts the policy gate validates.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.gates.base import GateContext
from app.ports.post_purchase import OrderView, PostPurchaseBackend
from app.returns.amazon_policy import ReturnFacts
from app.tools.registry import ToolArgumentError, ToolRegistry, ToolResult

LIST_ORDERS_SPEC = ToolSpec(
    name="list_orders",
    description=(
        "List the customer's own orders (id, status, dates, total). Use this when they "
        "ask about their orders without naming one, then call get_order_status with an "
        "id from the result."
    ),
    parameters={
        "type": "object",
        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 25}},
    },
)


def _summary(order: OrderView) -> dict[str, Any]:
    """The shape the transcript's orders card expects."""
    if order.delivered_at:
        status = "delivered"
    elif "FULFILLED" in order.fulfillment_status.upper():
        status = "shipped"
    else:
        status = "processing"
    return {
        "id": order.id,
        "status": status,
        "placed_at": order.created_at,
        "delivered_at": order.delivered_at,
        "total": order.total,
        "item_count": sum(line.quantity for line in order.line_items),
    }


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


def _order_dict(order: OrderView, returnable: list[Any]) -> dict[str, Any]:
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


def _resolve_item(returnable: list[Any], arguments: dict[str, Any]) -> str:
    """Resolve the item a proposal targets, or raise the tool's own error.

    Mirrors the old handler: a short ``item_ref`` is preferred over copying a long
    id, and the model's arguments are validated *before* the gates run.
    """
    fli_id = str(arguments.get("fulfillment_line_item_id", ""))
    ref = arguments.get("item_ref")
    if ref is not None:
        try:
            index = int(ref)
        except (TypeError, ValueError):
            index = 0
        if not 1 <= index <= len(returnable):
            raise ToolArgumentError(
                {
                    "error": "item_ref out of range",
                    "valid_refs": list(range(1, len(returnable) + 1)),
                }
            )
        return returnable[index - 1].fulfillment_line_item_id
    valid_ids = [item.fulfillment_line_item_id for item in returnable]
    if returnable and fli_id not in valid_ids:
        raise ToolArgumentError(
            {
                "error": "unknown item; pass item_ref instead",
                "valid_refs": list(range(1, len(returnable) + 1)),
                "items": [item.title for item in returnable],
            }
        )
    return fli_id


def register_post_purchase_tools(
    registry: ToolRegistry,
    backend: PostPurchaseBackend,
    *,
    now: datetime | None = None,
) -> None:
    """Register the read tools and the (side-effect-free) proposal tool.

    Gates (policy, tenancy) are supplied by the registry's gate set, not here, so
    a surface cannot forget them (046 hardening). ``now`` pins the clock for
    deterministic evaluations; production leaves it ``None`` (wall clock).
    """
    clock = now or datetime.now(UTC)

    async def order_context(name: str, arguments: dict[str, Any], session: Session) -> GateContext:
        order_id = str(arguments.get("order_id", ""))
        order = await backend.get_order(order_id) if order_id else None
        return GateContext(session=session, order=order, now=clock)

    async def propose_context(
        name: str, arguments: dict[str, Any], session: Session
    ) -> GateContext:
        decision = str(arguments.get("decision", "")).strip().lower()
        if decision not in _DECISIONS:
            raise ToolArgumentError("decision must be one of eligible|ineligible|escalate")
        order_id = str(arguments.get("order_id", ""))
        order = await backend.get_order(order_id) if order_id else None
        returnable = await backend.returnable_items(order_id) if order_id else []
        fli_id = _resolve_item(returnable, arguments)
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
        context = GateContext(
            session=session,
            order=order,
            now=clock,
            facts=facts,
            proposed=decision,
        )
        context.subject = {"fulfillment_line_item_id": fli_id, "facts": facts}
        return context

    async def list_orders(arguments: dict[str, Any], session: Session) -> ToolResult:
        # The listing is scoped by the authenticated principal, never by a value the
        # model supplies: without a principal this refuses instead of widening the query
        # to the whole shop.
        customer = str(getattr(session, "customer_id", "") or "")
        if not customer:
            return ToolResult(
                content=json.dumps(
                    {
                        "orders": [],
                        "accessible": False,
                        "reason": "no authenticated customer",
                        "guidance": "Ask the customer to sign in, or for the order number.",
                    }
                ),
                component="orders",
                payload={"items": []},
            )
        limit = max(1, min(25, int(arguments.get("limit", 10))))
        orders = await backend.list_orders(customer, limit)
        items = [_summary(order) for order in orders]
        session.remember_ids([order.id for order in orders])
        return ToolResult(
            content=json.dumps({"orders": items}),
            component="orders",
            payload={"items": items},
        )

    async def get_order_status(
        arguments: dict[str, Any], session: Session, context: GateContext
    ) -> ToolResult:
        order = context.order
        order_id = str(arguments.get("order_id", ""))
        if not isinstance(order, OrderView):
            return ToolResult(content=f"unknown order: {order_id}", status="error")
        session.remember_ids([order.id])
        # order.id is the resolved global id: never pass the customer-facing number
        # to a backend that expects a global id.
        returnable = await backend.returnable_items(order.id)
        return ToolResult(content=json.dumps(_order_dict(order, returnable)), component="order")

    async def list_returnable_items(
        arguments: dict[str, Any], session: Session, context: GateContext
    ) -> ToolResult:
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
        return ToolResult(
            content=json.dumps(payload),
            component="returnable_items",
            payload={"items": payload},
        )

    async def propose_return_decision(
        arguments: dict[str, Any], session: Session, context: GateContext
    ) -> ToolResult:
        subject = context.subject if isinstance(context.subject, dict) else {}
        fli_id = str(subject.get("fulfillment_line_item_id", ""))
        record: dict[str, Any] = {
            "order_id": str(arguments.get("order_id", "")),
            "fulfillment_line_item_id": fli_id,
            "decision": str(arguments.get("decision", "")).strip().lower(),
            "cited_clauses": [str(c) for c in arguments.get("cited_clauses", [])],
        }
        # The gate re-derives the decision and its clause ids are authoritative, so
        # the proposal cites the harness's clauses, not the model's recollection
        # (model proposes, harness disposes).
        if context.gate_clauses is not None:
            record["cited_clauses"] = list(context.gate_clauses)
            record["validated"] = True
        return ToolResult(content=json.dumps(record), component="return_decision")

    registry.register(LIST_ORDERS_SPEC, list_orders, effect="read")
    registry.register(
        GET_ORDER_SPEC,
        get_order_status,
        effect="read",
        context=order_context,
        consumes_context=True,
    )
    registry.register(
        RETURNABLE_SPEC,
        list_returnable_items,
        effect="read",
        context=order_context,
        consumes_context=True,
    )
    registry.register(
        PROPOSE_SPEC,
        propose_return_decision,
        effect="proposal",
        context=propose_context,
        consumes_context=True,
    )
