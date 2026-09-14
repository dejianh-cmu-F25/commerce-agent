"""Tenancy gate: a customer may act only on their own orders (feature 046, INV-7).

The harness enforces this, not the prompt. A request that names another
customer's order is blocked before anything is read or written.
"""

from __future__ import annotations

from app.gates.base import GateContext, GateResult


class TenancyGate:
    name = "tenancy"

    def check(self, context: GateContext) -> GateResult:
        order = context.order
        if order is None:
            return GateResult.allow()  # nothing to scope yet
        customer = getattr(context.session, "customer_id", "") or ""
        if not customer:
            return GateResult.block("no authenticated customer")
        if order.customer_id != customer:
            return GateResult.block("order belongs to another customer")
        return GateResult.allow()
