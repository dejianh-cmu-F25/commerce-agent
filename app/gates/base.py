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

    @classmethod
    def allow(cls) -> GateResult:
        return cls(True)

    @classmethod
    def block(cls, reason: str) -> GateResult:
        return cls(False, reason)


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
