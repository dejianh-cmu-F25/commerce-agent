"""Post-purchase tools: order status and a render-only return request (014).

Orders come only from the storefront (P4); the session may reference only ids the
storefront returned. ``start_return`` records a request and renders it — it never
refunds, charges, or changes the order (P3).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.core.session import Session
from app.core.types import Order, ToolSpec
from app.ports.storefront import StorefrontBackend
from app.returns.policy import return_eligibility
from app.tools.registry import ToolRegistry, ToolResult

LIST_ORDERS_SPEC = ToolSpec(
    name="list_orders",
    description=(
        "List the customer's orders (id, status, dates, total). Call this before "
        "answering any question about an order."
    ),
    parameters={"type": "object", "properties": {}},
)

ORDER_STATUS_SPEC = ToolSpec(
    name="get_order_status",
    description=(
        "Get the status, items, and dates of one order by its id. Only ids returned "
        "by list_orders are valid."
    ),
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The id from list_orders."}},
        "required": ["order_id"],
    },
)

START_RETURN_SPEC = ToolSpec(
    name="start_return",
    description=(
        "Start a return for an item on a delivered order, if it is inside the return "
        "window. This records a request only; it does not refund or change the order."
    ),
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The id from list_orders."},
            "product_id": {"type": "string", "description": "The item to return (e.g. P-101)."},
        },
        "required": ["order_id", "product_id"],
    },
)


def _summary(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "status": order.status,
        "placed_at": order.placed_at,
        "delivered_at": order.delivered_at,
        "total": order.total,
        "item_count": sum(item.quantity for item in order.items),
    }


def _detail(order: Order, window_days: int) -> dict[str, Any]:
    return {
        "id": order.id,
        "status": order.status,
        "placed_at": order.placed_at,
        "delivered_at": order.delivered_at,
        "total": order.total,
        "window_days": window_days,
        "items": [
            {
                "product_id": item.product_id,
                "title": item.title,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
            }
            for item in order.items
        ],
    }


def register_order_tools(
    registry: ToolRegistry, storefront: StorefrontBackend, window_days: int
) -> None:
    async def _list_orders(_arguments: dict[str, Any], session: Session) -> ToolResult:
        orders = storefront.list_orders(session.customer_id)
        session.remember_ids([order.id for order in orders])
        items = [_summary(order) for order in orders]
        return ToolResult(
            content=json.dumps({"orders": items}),
            component="orders" if items else None,
            payload={"items": items} if items else None,
        )

    async def _get_order_status(arguments: dict[str, Any], session: Session) -> ToolResult:
        order_id = str(arguments.get("order_id", "")).strip()
        if not session.knows(order_id):
            return ToolResult(
                content=json.dumps(
                    {"error": "unknown order id; call list_orders first", "order_id": order_id}
                ),
                status="error",
            )
        order = storefront.get_order(session.customer_id, order_id)
        if order is None:
            return ToolResult(
                content=json.dumps({"error": "order not found", "order_id": order_id}),
                status="error",
            )
        detail = _detail(order, window_days)
        return ToolResult(content=json.dumps(detail), component="order", payload=detail)

    async def _start_return(arguments: dict[str, Any], session: Session) -> ToolResult:
        order_id = str(arguments.get("order_id", "")).strip()
        product_id = str(arguments.get("product_id", "")).strip()
        if not session.knows(order_id):
            return ToolResult(
                content=json.dumps(
                    {"error": "unknown order id; call list_orders first", "order_id": order_id}
                ),
                status="error",
            )
        order = storefront.get_order(session.customer_id, order_id)
        if order is None:
            return ToolResult(
                content=json.dumps({"error": "order not found", "order_id": order_id}),
                status="error",
            )

        eligible, reason = return_eligibility(order, product_id, window_days)
        if not eligible:
            return ToolResult(
                content=json.dumps({"eligible": False, "reason": reason, "order_id": order_id}),
                status="error",
            )

        item = next(line for line in order.items if line.product_id == product_id)
        payload = {
            "order_id": order_id,
            "product_id": product_id,
            "title": item.title,
            "quantity": item.quantity,
            "status": "requested",
            "created_at": datetime.now(UTC).isoformat(),
            "window_days": window_days,
            "refunded": False,
        }
        return ToolResult(
            content=json.dumps({**payload, "reason": reason}),
            component="return",
            payload=payload,
        )

    registry.register(LIST_ORDERS_SPEC, _list_orders)
    registry.register(ORDER_STATUS_SPEC, _get_order_status)
    registry.register(START_RETURN_SPEC, _start_return)
