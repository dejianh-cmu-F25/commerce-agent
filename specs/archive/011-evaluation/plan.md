# Implementation Plan: Evaluation Harness

**Branch**: `011-evaluation` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/011-evaluation/spec.md`

## Summary

Add `evals/` with a gold set of scenarios and a runner that replays them with the
scripted `MockLLMClient` over the real loop/tools/stores, asserting deterministic
outcomes (tool sequence, cart, components). Exit non-zero on failure; run it in
the local gate. No new dependencies; keyless.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: existing (`MockLLMClient`, tool registry, stores)

**Storage**: in-memory storefront + a temp SQLite merchant per run

**Testing**: the harness itself is run by `pytest` and by `scripts/ci.sh`

**Target Platform**: dev/CI (no server)

**Performance Goals**: sub-second

**Constraints**: keyless; deterministic; no prose assertions (TT-2)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P7 evals first-class | gold set + gate | PASS |
| TT-2 keyless replay | scripted LLM; deterministic outcomes only | PASS |
| HR-8 evaluate the harness with deterministic mock tools | real tools, scripted model | PASS |
| P8 reproducible | no key/network | PASS |
| P6 simplicity | pure Python; no deps | PASS |

## Project Structure

```text
evals/
├── __init__.py
├── scenarios.py   # Scenario + SCENARIOS
└── run.py         # run_all(), main()
tests/integration/test_evals.py
scripts/ci.sh      # + Evals step
pyproject.toml     # pyright include "evals"
```

## Complexity Tracking

> No constitution violations; nothing to justify.
