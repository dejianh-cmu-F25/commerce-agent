# Implementation Plan: Scenario Runner

**Branch**: `016-scenario-runner` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/016-scenario-runner/spec.md`

## Summary

Extract the keyless scenario execution from `evals/run.py` into a reusable
`evals/runner.py` returning structured results (name, ok, failures, tools,
components). The gate CLI and a new web Scenario Runner both call it. Add
`GET /scenarios` and `POST /scenarios/run`, and a Scenarios tab. The header gains
a fifth tab and wraps/scolls so it stays usable at 375px. No new dependency.

## Technical Context

**Language/Version**: Python 3.13; React 19 + TypeScript (frontend)

**Primary Dependencies**: none new (reuses the eval harness and existing stack)

**Storage**: per-run in-memory/temp resources; the live stores are untouched

**Testing**: `pytest` (integration: `/scenarios` endpoints; existing eval test);
a browser checkpoint

**Target Platform**: server + browser

**Performance Goals**: all scenarios in well under a second (scripted model)

**Constraints**: keyless, deterministic, isolated from live state (P3, P7, P8)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes, harness disposes | scenarios run the real loop with a scripted model; merchant assertions still check no auto-apply | PASS |
| P7 evals are first-class | the browser runs the same gold scenarios as the gate | PASS |
| P8 reproducible | keyless; no provider call | PASS |
| HR-8 evaluate with mock tools | the runner is the mock-driven harness | PASS |
| WV-3 component registry | the view renders registered component names as chips | PASS |
| WV-4 Scenario Runner + Observability | this feature adds the missing Scenario Runner | PASS |
| WV-6 UI states | empty/loading/running/success/error/disabled defined | PASS |
| WV-8 responsive | header wraps/scolls at 375px; rows wrap | PASS |
| RD-1 resilience | a runner error surfaces inline; the app stays usable | PASS |
| HR-11 extension point | a new scenario is data in `evals/scenarios.py`, picked up by both surfaces | PASS |

## Project Structure

```text
evals/
├── runner.py     # NEW: ScenarioResult + run_scenarios (shared)
└── run.py        # thin CLI over the runner (unchanged output/exit code)
web/main.py       # GET /scenarios; POST /scenarios/run
frontend/src/
├── lib/scenarios.ts                    # NEW: API client + types
├── components/app/scenario-runner.tsx  # NEW
└── App.tsx                             # Scenarios tab; responsive header
tests/integration/test_scenarios_api.py # NEW
docs/architecture.md                    # WV-4 note
docs/notes/implemented/architecture/...-scenario-runner.md
```

## Design decisions

- **One runner, two surfaces.** The execution moves to `evals/runner.py`; the CLI
  and the endpoint both call `run_scenarios`, so results cannot drift (SC-001).
- **Isolation by construction.** Each scenario builds fresh in-memory storefront
  and memory and a temporary SQLite for the merchant, exactly as the gate does, so
  a web run cannot touch live state (P3, RD-2).
- **Catalog endpoint returns data, not code.** `GET /scenarios` serializes only
  name/user text/expected tools/components; the scripted turns stay server-side.
- **Header wraps.** The tab group and controls wrap (and the tab group scrolls
  inside itself) so the fifth tab does not break the 375px layout (WV-8).

## Complexity Tracking

> No constitution violations. One loop-adjacent refactor (eval runner extraction)
> with no behavior change; no new dependency.
