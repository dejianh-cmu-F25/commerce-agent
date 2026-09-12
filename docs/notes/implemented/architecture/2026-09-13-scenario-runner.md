# Agent Note: The Scenario Runner reuses the eval harness, keylessly

Status: implemented (2026-09-13) — feature `016-scenario-runner`

## Problem

WV-4 requires the web app to provide a Scenario Runner, the README advertises
one, and none existed. Adding one raised a cross-cutting question: how does the
browser run the gold scenarios without duplicating the eval logic, spending
budget, or touching live state?

## Alternatives considered

- **Duplicate the scenario logic in the web layer.** Fast to write, but the gate
  and the browser would drift, and a "passing" browser run would mean less.
  Rejected.
- **Call the LLM for real in the runner.** Realistic, but needs a key, spends
  budget, and is nondeterministic — the opposite of what an eval needs (P7, P8).
  Rejected.
- **Move scenarios/runner into `app/` and make `evals/` a thin CLI.** Cleaner
  layering, but churns the eval harness the gate and tests already depend on, for
  no functional gain. Rejected.
- **Stream results as each scenario finishes.** Nicer UX for a slow suite, but the
  suite is sub-second with a scripted model. Rejected as over-building.

## Decision

- **Extract the execution into `evals/runner.py`.** `run_scenarios()` returns
  structured results (name, ok, failures, actual tools, actual components); the
  gate CLI (`evals/run.py`) and the web both call it, so they cannot drift.
- **The runner is keyless and isolated by construction.** It builds fresh
  in-memory storefront/memory and a temporary SQLite for the merchant per
  scenario, exactly as the gate does, so a browser run never reads or mutates the
  live session, storefront, merchant store, customer memory, or budget (P3, RD-2).
- **The catalog endpoint returns data, not code.** `GET /scenarios` serializes
  only name, user text, and expected tools/components; the scripted turns stay
  server-side.
- **The header wraps and the tab group scrolls** so the fifth tab keeps the app
  usable at 375px with no page-level horizontal scroll (WV-8).

## Consequences

- Adding a scenario to `evals/scenarios.py` surfaces it in the gate and the
  browser with no further wiring (HR-11).
- `web` now imports `evals`; the eval harness is part of the runtime for this
  reviewer surface. This is deliberate: the runner is a first-class harness
  capability, not test-only code.
- The runner executes all scenarios in one request; if the suite grows slow, it
  will need streaming or a background job (documented as the next step).
