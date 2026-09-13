# Feature Specification: Scenario Runner

**Feature Branch**: `016-scenario-runner`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add the web **Scenario Runner** required by WV-4: run the keyless gold
scenarios over the real loop and tools (scripted mock model) and show pass/fail,
the tool sequence, and the rendered components in the browser. Reuse the eval
harness so the gate CLI and the web cannot drift.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the gold scenarios from the browser (Priority: P1)

A reviewer opens the Scenarios view, runs the gold scenarios, and sees each
scenario's pass/fail with the tool sequence and components it exercised.

**Why this priority**: WV-4 requires a Scenario Runner, the README advertises one,
and none exists. Evals are first-class (P7); the browser is where a reviewer sees
them.

**Independent Test**: Call the run endpoint and assert every scenario passes and
the response includes each scenario's tools and components.

**Acceptance Scenarios**:

1. **Given** the app running, **When** the Scenarios view loads, **Then** it lists
   the gold scenarios with their user text and expected tools/components.
2. **Given** the list, **When** the reviewer runs all, **Then** each scenario
   shows pass/fail and its actual tool sequence and components.
3. **Given** a failing assertion, **When** the run completes, **Then** the
   scenario is marked failed and the failure reason is shown.

---

### User Story 2 - One runner, no drift (Priority: P1)

The gate CLI and the web run the same code, so their results are identical.

**Independent Test**: Run the scenarios via the CLI and via the endpoint and
assert the same names and pass/fail.

**Acceptance Scenarios**:

1. **Given** the reusable runner, **When** the gate CLI runs, **Then** it reports
   the same results as the web endpoint.
2. **Given** a new gold scenario, **When** it is added, **Then** it appears in both
   without further wiring.

---

### User Story 3 - Keyless, isolated, deterministic (Priority: P2)

A run needs no API key, spends nothing, and never touches the live session,
storefront, memory, or budget.

**Independent Test**: Run the endpoint with no key configured; assert it passes
and that the live session/storefront are unchanged.

**Acceptance Scenarios**:

1. **Given** no API key, **When** scenarios run, **Then** they pass (mock model).
2. **Given** a running app with live data, **When** scenarios run, **Then** the
   live session/storefront/memory/budget are unaffected.

---

### Edge Cases

- **Run in progress**: the Run control is disabled; a second run cannot start.
- **Runner error**: an unexpected error returns a failed result with the message,
  and the view shows an inline error; the app stays usable (RD-1).
- **Empty catalog**: if there are no scenarios, the view says so.
- **Slow run**: results stream in only at the end (one response); the view shows a
  running state meanwhile.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The eval harness MUST expose a reusable async runner returning, per
  scenario, its name, pass/fail, failures, tool sequence, and components.
- **FR-002**: The gate CLI (`evals/run.py`) MUST use that runner so the gate and
  the web cannot diverge; its output and exit code are unchanged.
- **FR-003**: The web MUST expose `GET /scenarios` returning the catalog: each
  scenario's name, user text, and expected tools/components.
- **FR-004**: The web MUST expose `POST /scenarios/run` that runs all scenarios
  and returns their results.
- **FR-005**: A run MUST be isolated: fresh in-memory/temporary resources; it MUST
  NOT read or mutate the live session store, storefront, merchant store, customer
  memory, or budget (P3, RD-2).
- **FR-006**: A run MUST be keyless and deterministic (scripted mock model); no
  provider call and no spend (P7, P8, HR-8).
- **FR-007**: The UI MUST provide a Scenarios view that lists the scenarios, runs
  them, and shows per-scenario pass/fail with tools and components.
- **FR-008**: The UI MUST define empty, loading/running, success, error, and
  disabled states; the Run control MUST be disabled while a run is in flight
  (WV-6).
- **FR-009**: The header MUST remain usable from 375px with the added tab: tabs
  wrap or scroll inside their own container with no page-level horizontal scroll
  (WV-8).

### Key Entities

- **Scenario**: a gold case (name, user text, scripted turns, expected tools and
  components, optional cart/memory expectations).
- **ScenarioResult**: the outcome of running one scenario (name, ok, failures,
  actual tools, actual components).

## UI Requirements

A new **Scenarios** view (a tab beside Chat / Traces / Merchant / Memory).

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | The catalog is empty | A line saying there are no scenarios |
| Loading | The catalog is being fetched | A "Loading…" line |
| Running | A run is in flight | A "Running…" indicator; the Run control is disabled |
| Success | A run completes | Each scenario with a pass/fail badge, its tools, and its components; a summary "N of M passed" |
| Error | The catalog or run fails | An inline error with Retry; failures per scenario are listed when the run itself succeeded |
| Disabled | A run is in flight | The Run control is disabled |

### Accessibility

- [ ] Tabs and the Run control are keyboard-operable with a visible focus ring.
- [ ] Results are announced politely when they change (`aria-live`).
- [ ] Pass/fail is conveyed by text, not color alone.
- [ ] Motion respects `prefers-reduced-motion`.

### Responsive & Theme

- [ ] The header wraps or scrolls its tab group so the app has no page-level horizontal scroll from 375px up.
- [ ] Scenario rows wrap their tool/component chips inside the card.
- [ ] Theme follows `prefers-color-scheme`.

## Web Acceptance

- The header exposes a **Scenarios** tab; selecting it lists the gold scenarios.
- Clicking **Run all** shows each scenario's pass/fail, tools, and components, and
  a summary count.
- Running does not require an API key and does not change the chat, traces,
  merchant, or memory views' data.

## Observability

- The run endpoint returns structured results; failures carry the assertion
  message so a broken scenario is diagnosable from the view.
- The runner is the same code the gate executes, so gate output and the browser
  agree.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: CLI and web return identical scenario names and pass/fail.
- **SC-002**: All gold scenarios pass in the web runner with no API key.
- **SC-003**: A run leaves the live session/storefront/memory/budget unchanged.
- **SC-004**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes with the feature enabled.
- **SC-005**: The header has no page-level horizontal scroll at 375px with the
  added tab.

## Assumptions

- The gold scenario set is the one in `evals/scenarios.py`; the runner adds no new
  scenarios.
- Running all scenarios is fast (scripted model, in-memory/temp stores), so a
  single request is acceptable; no streaming is needed.
- The Scenario Runner is a reviewer/dev surface, not a customer feature; it is
  reachable from the same app and needs no auth (consistent with Traces/Merchant).

## Measured Results

- The browser Scenario Runner reports **12/12** gold scenarios passing,
  keylessly, matching the gate CLI (one runner, no drift).
- Source: `evals/runner.py`; aggregate: [`specs/RESULTS.md`](../RESULTS.md).

## Real-World Coverage

- **Input distribution**: the gold scenarios (the catalog).
- **Data quality**: runs the real loop with fresh in-memory/temp resources.
- **Edge & failure modes**: a run error shows inline; the Run control is disabled
  while running.
- **Scale envelope**: 12 scenarios in one request; not measured (gap).
- **Degradation**: keyless; no provider needed.
- **Change evidence**: 12/12 (`specs/RESULTS.md`).
