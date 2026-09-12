"""Provenance gate: only server-issued ids may be written or rendered (P4)."""

from __future__ import annotations

from app.gates.base import GateContext, GateResult


class ProvenanceGate:
    name = "provenance"

    def check(self, context: GateContext) -> GateResult:
        unknown = [
            identifier for identifier in context.ids if not context.session.knows(identifier)
        ]
        if unknown:
            return GateResult.block(f"unknown id(s): {', '.join(unknown)}")
        return GateResult.allow()
