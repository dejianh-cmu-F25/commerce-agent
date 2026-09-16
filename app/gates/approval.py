"""Approval gate: money-adjacent completion needs a human (feature 046, INV-6).

``complete_checkout`` is HITL-gated: without an explicit ``approved=true`` the
gate blocks with a ``pending_approval`` payload, so no order is placed and no
charge is issued. Previously this was an inline ``if`` in the tool; it is now a
pluggable gate (046 hardening) that any HITL tool can adopt.
"""

from __future__ import annotations

from app.gates.base import APPROVAL, Applicability, GateContext, GateResult


class ApprovalGate:
    name = "approval"
    applies_to = Applicability(tools=frozenset({"complete_checkout"}))
    priority = APPROVAL

    def check(self, context: GateContext) -> GateResult:
        if bool(context.arguments.get("approved", False)):
            return GateResult.allow()
        return GateResult.block(
            "checkout requires human approval",
            component="checkout",
            payload={
                "session_id": str(context.arguments.get("session_id", "")),
                "status": "pending_approval",
                "charge_issued": False,
            },
        )
