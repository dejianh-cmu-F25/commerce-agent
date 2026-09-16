"""Build the standard gate set from configuration (046 hardening, PB-1).

One factory, used by every surface (web, MCP, CLI), so a gate cannot be left out
of one wiring site by mistake. The gates are selected and ordered **explicitly**
(PB-3); an unknown name fails loud (PB-1).
"""

from __future__ import annotations

from app.core.settings import Settings
from app.gates.approval import ApprovalGate
from app.gates.policy import PolicyGate
from app.gates.provenance import ProvenanceGate
from app.gates.registry import GateSet, order_gates
from app.gates.tenancy import TenancyGate
from app.returns.amazon_policy import AmazonPolicy, load_amazon_policy


def build_gate_set(settings: Settings, *, policy: AmazonPolicy | None = None) -> GateSet:
    """The production gate set: provenance, tenancy, approval, policy."""
    gates = [
        ProvenanceGate(),
        TenancyGate(),
        ApprovalGate(),
        PolicyGate(policy if policy is not None else load_amazon_policy()),
    ]
    config = settings.gates
    enabled = {gate.name for gate in gates} - set(config.disabled)
    ordered = order_gates(gates, enabled=enabled, order=config.order or None)
    return GateSet(ordered)
