"""Tenancy gate: a customer may act only on their own orders (feature 046, INV-7).

The harness enforces this, not the prompt. A request that names another
customer's order is blocked before anything is read or written.
"""

from __future__ import annotations

from app.gates.base import GateContext, GateResult


class TenancyGate:
    name = "tenancy"

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
        if not customer:
            return GateResult.block("order belongs to a customer; no authenticated customer")
        if owner != customer:
            return GateResult.block("order belongs to another customer")
        return GateResult.allow()
