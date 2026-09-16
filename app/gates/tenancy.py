"""Tenancy gate: a customer may act only on their own orders (feature 046, INV-7).

The harness enforces this, not the prompt. A request that names another
customer's order is blocked before anything is read or written. A refusal is not
an error: the status stays ``ok`` so the model relays it instead of retrying.
"""

from __future__ import annotations

from app.gates.base import AUTHORIZATION, Applicability, GateContext, GateResult

_GUIDANCE = (
    "Do not reveal or act on this order. Say you can only help with the customer's "
    "own orders and offer to look one of theirs up."
)


class TenancyGate:
    name = "tenancy"
    applies_to = Applicability(
        tools=frozenset({"get_order_status", "list_returnable_items", "propose_return_decision"})
    )
    priority = AUTHORIZATION

    def check(self, context: GateContext) -> GateResult:
        """An order that declares an owner may only be read by that customer.

        An order with no declared owner cannot leak anything, so it is allowed - that
        is what keeps the keyless fixtures (which carry no ownership) working. A
        declared owner raises the bar: the session must match it, and a session with
        no principal is refused rather than trusted, so the safe direction is the
        default.
        """
        order = context.order
        if order is None:
            return GateResult.allow()  # nothing to scope yet
        owner = str(getattr(order, "customer_id", "") or "")
        if not owner:
            return GateResult.allow()  # no declared owner: nothing to protect
        customer = str(getattr(context.session, "customer_id", "") or "")
        blocked_reason = ""
        if not customer:
            blocked_reason = "order belongs to a customer; no authenticated customer"
        elif owner != customer:
            blocked_reason = "order belongs to another customer"
        if not blocked_reason:
            return GateResult.allow()
        order_id = str(context.arguments.get("order_id") or getattr(order, "id", ""))
        return GateResult.block(
            blocked_reason,
            status="ok",
            component="order",
            payload={
                "order_id": order_id,
                "accessible": False,
                "reason": blocked_reason,
                "guidance": _GUIDANCE,
            },
        )
