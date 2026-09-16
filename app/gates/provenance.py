"""Provenance gate: only server-issued ids may be written or rendered (P4)."""

from __future__ import annotations

from app.gates.base import IDENTITY, Applicability, GateContext, GateResult


class ProvenanceGate:
    name = "provenance"
    # Preserve the shipped scope: the write that grounds ids today.
    applies_to = Applicability(tools=frozenset({"add_to_cart"}))
    priority = IDENTITY

    def check(self, context: GateContext) -> GateResult:
        unknown = [
            identifier for identifier in context.ids if not context.session.knows(identifier)
        ]
        if unknown:
            return GateResult.block(
                f"unknown id(s): {', '.join(unknown)}",
                payload={
                    "error": "unknown product id; search for it first",
                    "product_id": unknown[0],
                },
            )
        return GateResult.allow()
