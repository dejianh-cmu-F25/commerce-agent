"""Policy gate: validate a return proposal against the policy SoT (feature 046).

This is the harness's runtime "dispose" step. The model proposes a decision; this
gate re-derives it deterministically from the policy SoT and the order facts, and
blocks anything that contradicts the policy. Gates never mutate state (P3).
"""

from __future__ import annotations

from app.gates.base import POLICY, Applicability, GateContext, GateResult
from app.returns.amazon_policy import ELIGIBLE, AmazonPolicy, decide_return


class PolicyGate:
    name = "policy"
    applies_to = Applicability(tools=frozenset({"propose_return_decision"}))
    priority = POLICY

    def __init__(self, policy: AmazonPolicy, *, version: str | None = None) -> None:
        self._policy = policy
        self._version = version

    def check(self, context: GateContext) -> GateResult:
        if context.facts is None:
            return GateResult.block("no return facts to validate")
        decision = decide_return(
            context.facts, self._policy, now=context.now, version=self._version
        )
        detail = "; ".join(decision.reasons) or decision.decision
        cited = f" [{' '.join(decision.cited_clauses)}]" if decision.cited_clauses else ""
        clauses = tuple(decision.cited_clauses)
        if context.proposed:
            # Validating a *proposal*: it passes when it agrees with the engine.
            # An "ineligible" verdict is a correct answer, not a refused action.
            if context.proposed != decision.decision:
                reason = (
                    f"proposal {context.proposed!r} contradicts the policy "
                    f"({decision.decision!r}): {detail}{cited}"
                )
                return GateResult.block(
                    reason,
                    clauses,
                    payload={
                        "order_id": context.facts.order_id,
                        "fulfillment_line_item_id": context.facts.fulfillment_line_item_id,
                        "decision": context.proposed,
                        "cited_clauses": list(clauses),
                        "validated": False,
                        "policy": reason,
                    },
                )
            return GateResult.allow(clauses)
        if decision.decision == ELIGIBLE:
            return GateResult.allow(clauses)
        return GateResult.block(f"{decision.decision}: {detail}{cited}", clauses)
