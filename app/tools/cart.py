"""Cart tools: ``add_to_cart``, ``view_cart``, ``render_checkout``.

The cart is a proposal (P3): these tools mutate the session cart and render a
summary; nothing is charged and no order is placed. Only server-issued product
ids may be added (P4); titles and prices come from the storefront, never the
model.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.session import CartLine, Session
from app.core.types import ToolSpec
from app.gates.base import GateContext
from app.gates.pipeline import GatePipeline
from app.gates.provenance import ProvenanceGate
from app.ports.storefront import StorefrontBackend
from app.tools.registry import ToolRegistry, ToolResult

_PROVENANCE = GatePipeline([ProvenanceGate()])

ADD_TO_CART_SPEC = ToolSpec(
    name="add_to_cart",
    description=(
        "Add a product to the customer's cart by its server-issued id (e.g. P-101). "
        "Only ids returned by search_products are valid."
    ),
    parameters={
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "The id from a search result."},
            "quantity": {"type": "integer", "description": "How many (default 1).", "minimum": 1},
        },
        "required": ["product_id"],
    },
)

VIEW_CART_SPEC = ToolSpec(
    name="view_cart",
    description="Show the current cart: items, quantities, line totals and the total.",
    parameters={"type": "object", "properties": {}},
)

CHECKOUT_SPEC = ToolSpec(
    name="render_checkout",
    description=(
        "Render a checkout summary for the current cart. This only displays the order; "
        "it never charges and never places the order."
    ),
    parameters={"type": "object", "properties": {}},
)


def cart_payload(session: Session) -> dict[str, Any]:
    items = [
        {
            "product_id": line.product_id,
            "title": line.title,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "line_total": round(line.unit_price * line.quantity, 2),
        }
        for line in session.cart
    ]
    total = round(sum(item["line_total"] for item in items), 2)
    return {"items": items, "total": total}


def checkout_payload(session: Session) -> dict[str, Any]:
    payload = cart_payload(session)
    payload["charged"] = False
    return payload


def _clamp_quantity(value: Any) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, quantity)


def register_cart_tools(registry: ToolRegistry, storefront: StorefrontBackend) -> None:
    async def _add_to_cart(arguments: dict[str, Any], session: Session) -> ToolResult:
        product_id = str(arguments.get("product_id", "")).strip()
        if not _PROVENANCE.run(GateContext(session=session, ids=[product_id])).allowed:
            # P4: the model may only add ids the session has already seen.
            return ToolResult(
                content=json.dumps(
                    {"error": "unknown product id; search for it first", "product_id": product_id}
                ),
                status="error",
            )
        product = storefront.get(product_id)
        if product is None:
            return ToolResult(
                content=json.dumps({"error": "product not found", "product_id": product_id}),
                status="error",
            )

        quantity = _clamp_quantity(arguments.get("quantity", 1))
        line = next((item for item in session.cart if item.product_id == product_id), None)
        if line is None:
            session.cart.append(
                CartLine(
                    product_id=product.id,
                    title=product.title,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )
        else:
            line.quantity += quantity

        payload = cart_payload(session)
        return ToolResult(content=json.dumps(payload), component="cart", payload=payload)

    async def _view_cart(_arguments: dict[str, Any], session: Session) -> ToolResult:
        payload = cart_payload(session)
        return ToolResult(content=json.dumps(payload), component="cart", payload=payload)

    async def _render_checkout(_arguments: dict[str, Any], session: Session) -> ToolResult:
        payload = checkout_payload(session)
        return ToolResult(content=json.dumps(payload), component="checkout", payload=payload)

    registry.register(ADD_TO_CART_SPEC, _add_to_cart)
    registry.register(VIEW_CART_SPEC, _view_cart)
    registry.register(CHECKOUT_SPEC, _render_checkout)
