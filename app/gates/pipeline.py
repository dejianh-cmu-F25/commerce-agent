"""Gate pipeline: run gates in order and return the first block (feature 020).

Pluggable-gate hardening (046): the pipeline **aggregates** the clauses every
gate cites (previously a full pass returned an empty ``allow`` and dropped
them), stamps the blocking gate's name, and supports an explicit hit policy --
``first`` (short-circuit, default) or ``collect`` (evaluate every gate).
"""

from __future__ import annotations

from dataclasses import replace

from app.gates.base import Gate, GateContext, GateResult

HitPolicy = str  # "first" | "collect"


class GatePipeline:
    def __init__(self, gates: list[Gate], hit_policy: HitPolicy = "first") -> None:
        if hit_policy not in ("first", "collect"):
            raise ValueError(f"unknown hit_policy: {hit_policy!r}")
        self._gates = list(gates)
        self._hit_policy = hit_policy

    def run(self, context: GateContext) -> GateResult:
        clauses: list[str] = []
        blocks: list[GateResult] = []
        for gate in self._gates:
            result = gate.check(context)
            if not result.gate:
                result = replace(result, gate=gate.name)
            clauses.extend(result.cited_clauses)
            if not result.allowed:
                if self._hit_policy == "first":
                    return replace(result, cited_clauses=tuple(dict.fromkeys(clauses)))
                blocks.append(result)
        merged = tuple(dict.fromkeys(clauses))
        if blocks:
            first = blocks[0]
            return replace(
                first,
                reason="; ".join(block.reason for block in blocks if block.reason),
                gate=",".join(block.gate for block in blocks),
                cited_clauses=merged,
            )
        return GateResult(True, "", merged)
