"""Return-eligibility gate: wrap the return policy (feature 014, P3)."""

from __future__ import annotations

from app.core.types import Order
from app.gates.base import GateContext, GateResult
from app.returns.policy import return_eligibility


class ReturnEligibilityGate:
    name = "return_eligibility"

    def check(self, context: GateContext) -> GateResult:
        # The legacy gate belongs to the storefront path, where the context carries an
        # Order; the post-purchase path has the closed-loop PolicyGate instead.
        if not isinstance(context.order, Order):
            return GateResult.block("no order to return")
        allowed, reason = return_eligibility(
            context.order, context.product_id, context.window_days, now=context.now
        )
        return GateResult(allowed, reason)
