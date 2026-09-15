"""Gate contracts (feature 020).

A gate is a decision-only guardrail: it inspects a context and returns a
:class:`GateResult`. Gates never mutate state (P3); the caller owns effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.core.session import Session
from app.core.types import Order
from app.returns.amazon_policy import ReturnFacts


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str = ""
    cited_clauses: tuple[str, ...] = ()

    @classmethod
    def allow(cls, cited_clauses: tuple[str, ...] = ()) -> GateResult:
        return cls(True, "", cited_clauses)

    @classmethod
    def block(cls, reason: str, cited_clauses: tuple[str, ...] = ()) -> GateResult:
        return cls(False, reason, cited_clauses)


@dataclass
class GateContext:
    session: Session
    ids: list[str] = field(default_factory=list)
    order: Order | None = None
    product_id: str = ""
    window_days: int = 30
    now: datetime | None = None
    facts: ReturnFacts | None = None
    proposed: str = ""  # the model's proposed decision, when there is one


class Gate(Protocol):
    name: str

    def check(self, context: GateContext) -> GateResult:
        """Return whether the action is allowed, with a reason when blocked."""
        ...
