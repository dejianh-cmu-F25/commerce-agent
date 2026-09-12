# Tasks: Gates

**Feature**: `020-gates` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/gates/base.py` (`GateResult`, `Gate`, `GateContext`)
- [x] T002 `app/gates/provenance.py` (`ProvenanceGate`)
- [x] T003 `app/gates/returns.py` (`ReturnEligibilityGate`)
- [x] T004 `app/gates/pipeline.py` (`GatePipeline`)
- [x] T005 Refactor `app/tools/cart.py` to use the provenance gate (same output)
- [x] T006 Refactor `app/tools/orders.py` to use both gates (same output)
- [x] T007 [P] `tests/unit/test_gates.py`
- [x] T008 `docs/architecture.md`; Agent Note
- [x] T009 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001 before T002–T004.
- T002–T004 before T005–T007.
- T009 last.
