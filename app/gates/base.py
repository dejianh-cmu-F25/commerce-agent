"""Gate contracts (feature 020; pluggable gates, 046 hardening).

A gate is a **decision-only** guardrail: it inspects a :class:`GateContext` and
returns a :class:`GateResult`. Gates never mutate state (P3); the caller owns
effects. Gates declare *where* they apply (``applies_to``) and *when* they run
(``priority``), so adding a gate is one class plus one registration line -- no
tool changes (046 hardening).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

from app.core.session import Session
from app.core.types import Order
from app.ports.post_purchase import OrderView
from app.returns.amazon_policy import ReturnFacts

# What a tool does; a gate can target a whole effect class (e.g. every write).
Effect = Literal["read", "write", "proposal", "irreversible"]

# Effects that must be covered by at least one gate (fail-closed, 046 hardening).
# `proposal` and `irreversible` are the money-adjacent classes: a tool in one of
# them with no gate is refused rather than run. Plain `write` tools are gated by
# the gate's own `applies_to` (e.g. provenance on add_to_cart) but are not
# fail-closed here, to avoid blocking staged/simulated writes.
GATED_EFFECTS = frozenset({"proposal", "irreversible"})

# Default ordering tiers (lower runs first). Gates pick a tier, or any int.
# Cheap identity/origin checks run first; the policy engine later; global
# guardrails (rate limit, PII) last. Config may override the order (PB-1/PB-3).
IDENTITY = 100
AUTHORIZATION = 200
APPROVAL = 300
POLICY = 400
GUARDRAIL = 500


@dataclass(frozen=True)
class Applicability:
    """Which tools a gate applies to. An empty set on an axis means "any"."""

    tools: frozenset[str] = field(default_factory=frozenset)
    effects: frozenset[str] = field(default_factory=frozenset)

    def matches(self, tool: str, effect: str) -> bool:
        if self.tools and tool not in self.tools:
            return False
        if self.effects and effect not in self.effects:
            return False
        return True


# Applies to every tool (a "global" gate).
ALL = Applicability()


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str = ""
    cited_clauses: tuple[str, ...] = ()
    # The gate that produced this result (stamped by the pipeline).
    gate: str = ""
    # A refusal is not always an error: tenancy refuses with status "ok" so the
    # model relays it instead of retrying. The gate declares the status.
    status: str = "error"
    # Optional exact tool output when this gate blocks (preserves richer shapes
    # such as the tenancy "accessible: false" payload).
    payload: dict[str, Any] | None = None
    component: str | None = None

    @classmethod
    def allow(cls, cited_clauses: tuple[str, ...] = ()) -> GateResult:
        return cls(True, "", tuple(cited_clauses))

    @classmethod
    def block(
        cls,
        reason: str,
        cited_clauses: tuple[str, ...] = (),
        *,
        gate: str = "",
        status: str = "error",
        payload: dict[str, Any] | None = None,
        component: str | None = None,
    ) -> GateResult:
        return cls(False, reason, tuple(cited_clauses), gate, status, payload, component)


@dataclass
class GateContext:
    """Everything a gate may inspect. Built by the registry from the tool call."""

    session: Session
    ids: list[str] = field(default_factory=list)
    # Either the storefront's Order or the post-purchase OrderView: gates read the
    # fields they need (the tenancy gate reads the owner).
    order: Order | OrderView | None = None
    product_id: str = ""
    window_days: int = 30
    now: datetime | None = None
    facts: ReturnFacts | None = None
    proposed: str = ""  # the model's proposed decision, when there is one
    # Plugin fields (046 hardening): the call itself, so a generic gate needs no
    # tool change.
    tool: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    effect: str = "read"
    tags: tuple[str, ...] = ()
    # An optional domain object the tool resolved (e.g. the order it is acting on).
    subject: Any = None
    # The clauses the gates cited on allow (set by the registry), so a tool that
    # consumes the context can attach the authoritative citations to its output.
    gate_clauses: tuple[str, ...] | None = None


class Gate(Protocol):
    name: str
    applies_to: Applicability
    priority: int

    def check(self, context: GateContext) -> GateResult:
        """Return whether the action is allowed, with a reason when blocked."""
        ...
