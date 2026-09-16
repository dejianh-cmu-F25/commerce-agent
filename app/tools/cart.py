"""Cart tools: ``add_to_cart``, ``view_cart``, ``render_checkout``.

The cart is a proposal (P3): these tools mutate the session cart and render a
summary; nothing is charged and no order is placed. Only server-issued product
ids may be added (P4); titles and prices come from the storefront, never the
model. The provenance gate (in the registry's gate set) enforces the id origin at
the write (046 hardening).
"""

from __future__ import annotations

import json
from typing import Any

from app.adapters.cart_session import SessionCart
from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.storefront import StorefrontBackend
from app.tools.registry import ToolRegistry, ToolResult

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


def register_cart_tools(
    registry: ToolRegistry,
    storefront: StorefrontBackend,
    cart: Any | None = None,
) -> None:
    """Register the cart tools.

    ``cart`` is the storage behind them (``app/ports/cart.py``): the session-backed
    provider by default, a Storefront-backed one when configured. Either way the lines
    are mirrored onto the session, which is what the transcript and the persistence
    layer read.
    """
    cart_backend = cart if cart is not None else SessionCart()

    async def _add_to_cart(arguments: dict[str, Any], session: Session) -> ToolResult:
        product_id = str(arguments.get("product_id", "")).strip()
        product = storefront.get(product_id)
        if product is None:
            return ToolResult(
                content=json.dumps({"error": "product not found", "product_id": product_id}),
                status="error",
            )

        quantity = _clamp_quantity(arguments.get("quantity", 1))
        try:
            cart_backend.add(session, product, quantity)
        except Exception as exc:  # a cart failure is the customer's answer, not a crash
            return ToolResult(
                content=json.dumps({"error": "could not add to the cart", "detail": str(exc)}),
                status="error",
            )

        payload = cart_payload(session)
        return ToolResult(content=json.dumps(payload), component="cart", payload=payload)

    async def _view_cart(_arguments: dict[str, Any], session: Session) -> ToolResult:
        payload = cart_payload(session)
        return ToolResult(content=json.dumps(payload), component="cart", payload=payload)

    async def _render_checkout(_arguments: dict[str, Any], session: Session) -> ToolResult:
        payload = checkout_payload(session)
        return ToolResult(content=json.dumps(payload), component="checkout", payload=payload)

    registry.register(ADD_TO_CART_SPEC, _add_to_cart, effect="write", id_args=("product_id",))
    registry.register(VIEW_CART_SPEC, _view_cart, effect="read")
    registry.register(CHECKOUT_SPEC, _render_checkout, effect="read")
