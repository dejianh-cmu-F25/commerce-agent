"""Gate registry and explicit ordering (046 hardening, PB-1 / PB-3).

A ``GateSet`` is an ordered bag of gate instances. The order is resolved
**explicitly** by :func:`order_gates` -- never hidden inside a ``run()`` -- so it
can be inspected, snapshot-tested and configured. A misconfiguration (an unknown
gate name, a duplicate) fails loud (PB-1), never silently drops a gate.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.gates.base import ALL, Applicability, Gate


class GateConfigError(RuntimeError):
    """Raised when gate configuration is invalid (PB-1: fail loud)."""


def _applicability(gate: Gate) -> Applicability:
    return getattr(gate, "applies_to", ALL)


def _priority(gate: Gate) -> int:
    return int(getattr(gate, "priority", 1000))


def order_gates(
    gates: Iterable[Gate],
    *,
    enabled: set[str] | None = None,
    order: Sequence[str] | None = None,
) -> list[Gate]:
    """Resolve the gate order explicitly (PB-3).

    ``enabled`` keeps only the named gates (unknown names fail loud); ``order``
    pins the named gates first, in that order, with the rest placed by priority.
    Ties break by name so the result is stable and snapshot-testable.
    """
    gates = list(gates)
    named: dict[str, Gate] = {}
    for gate in gates:
        if gate.name in named:
            raise GateConfigError(f"duplicate gate name: {gate.name!r}")
        named[gate.name] = gate

    if enabled is not None:
        unknown = sorted(set(enabled) - set(named))
        if unknown:
            raise GateConfigError(f"unknown gate(s) in config: {unknown}")
        named = {name: gate for name, gate in named.items() if name in enabled}

    if order:
        unknown = [name for name in order if name not in named]
        if unknown:
            raise GateConfigError(f"unknown gate(s) in order: {unknown}")
        pinned = [named[name] for name in order]
        rest = sorted(
            (gate for name, gate in named.items() if name not in set(order)),
            key=lambda gate: (_priority(gate), gate.name),
        )
        return pinned + rest

    return sorted(named.values(), key=lambda gate: (_priority(gate), gate.name))


class GateSet:
    """An ordered set of gates; selects the ones that apply to a tool call."""

    def __init__(self, gates: Iterable[Gate]) -> None:
        self._gates = tuple(gates)

    def select(self, tool: str, effect: str) -> list[Gate]:
        return [gate for gate in self._gates if _applicability(gate).matches(tool, effect)]

    def covers(self, tool: str, effect: str) -> bool:
        return bool(self.select(tool, effect))

    def all(self) -> tuple[Gate, ...]:
        return self._gates

    def names(self) -> tuple[str, ...]:
        return tuple(gate.name for gate in self._gates)

    def __len__(self) -> int:
        return len(self._gates)

    def __iter__(self):
        return iter(self._gates)
