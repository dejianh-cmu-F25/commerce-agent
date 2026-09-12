"""Gate pipeline: run gates in order and return the first block (feature 020)."""

from __future__ import annotations

from app.gates.base import Gate, GateContext, GateResult


class GatePipeline:
    def __init__(self, gates: list[Gate]) -> None:
        self._gates = list(gates)

    def run(self, context: GateContext) -> GateResult:
        for gate in self._gates:
            result = gate.check(context)
            if not result.allowed:
                return result
        return GateResult.allow()
