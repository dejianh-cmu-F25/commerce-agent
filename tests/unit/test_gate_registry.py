"""Unit tests for the pluggable gate registry, ordering and pipeline (046 hardening)."""

from __future__ import annotations

import pytest

from app.core.session import Session
from app.gates.base import ALL, Applicability, GateContext, GateResult
from app.gates.pipeline import GatePipeline
from app.gates.registry import GateConfigError, GateSet, order_gates


class _Gate:
    def __init__(self, name: str, priority: int, *, applies_to=ALL, allowed=True, clauses=()):
        self.name = name
        self.priority = priority
        self.applies_to = applies_to
        self._allowed = allowed
        self._clauses = clauses

    def check(self, context: GateContext) -> GateResult:
        return (
            GateResult.allow(self._clauses)
            if self._allowed
            else GateResult.block("no", self._clauses)
        )


def test_order_gates_uses_priority_tiers():
    gates = order_gates([_Gate("b", 200), _Gate("a", 100), _Gate("c", 300)])
    assert [g.name for g in gates] == ["a", "b", "c"]


def test_order_gates_pins_named_gates_first():
    gates = order_gates([_Gate("a", 100), _Gate("b", 200), _Gate("c", 300)], order=["c"])
    assert [g.name for g in gates] == ["c", "a", "b"]


def test_unknown_gate_in_config_fails_loud():
    with pytest.raises(GateConfigError):
        order_gates([_Gate("a", 100)], enabled={"a", "ghost"})
    with pytest.raises(GateConfigError):
        order_gates([_Gate("a", 100)], order=["ghost"])


def test_duplicate_gate_name_fails_loud():
    with pytest.raises(GateConfigError):
        order_gates([_Gate("a", 100), _Gate("a", 200)])


def test_gate_set_selects_by_tool_and_effect():
    by_tool = _Gate("t", 100, applies_to=Applicability(tools=frozenset({"add_to_cart"})))
    by_effect = _Gate("e", 100, applies_to=Applicability(effects=frozenset({"irreversible"})))
    everywhere = _Gate("g", 100)
    gate_set = GateSet([by_tool, by_effect, everywhere])

    assert [g.name for g in gate_set.select("add_to_cart", "write")] == ["t", "g"]
    assert [g.name for g in gate_set.select("complete_checkout", "irreversible")] == ["e", "g"]
    assert [g.name for g in gate_set.select("view_cart", "read")] == ["g"]
    assert gate_set.covers("complete_checkout", "irreversible")
    assert not GateSet([by_tool]).covers("view_cart", "read")


def test_pipeline_aggregates_cited_clauses_on_allow():
    pipeline = GatePipeline([_Gate("a", 1, clauses=("c1",)), _Gate("b", 2, clauses=("c2",))])
    result = pipeline.run(GateContext(session=Session(id="s")))
    assert result.allowed
    assert result.cited_clauses == ("c1", "c2")


def test_pipeline_first_short_circuits_and_stamps_the_gate():
    pipeline = GatePipeline([_Gate("a", 1, allowed=False), _Gate("b", 2)])
    result = pipeline.run(GateContext(session=Session(id="s")))
    assert not result.allowed
    assert result.gate == "a"


def test_pipeline_collect_runs_every_gate():
    pipeline = GatePipeline(
        [_Gate("a", 1, allowed=False), _Gate("b", 2, allowed=False)], hit_policy="collect"
    )
    result = pipeline.run(GateContext(session=Session(id="s")))
    assert not result.allowed
    assert result.gate == "a,b"
