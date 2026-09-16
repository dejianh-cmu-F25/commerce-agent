# Browser checkpoint: 016-scenario-runner

Constitution SR-4 / SR-5. The Scenario Runner is a new browser surface (WV-4), so
a checkpoint is recorded.

## Card

```
Checkpoint: 016 scenario runner
URL:    http://127.0.0.1:8000
Steps:
  1. Open the Scenarios tab; confirm the gold scenarios are listed.
  2. Click "Run all".
  3. Confirm each scenario shows Pass with its tools and components, and "11/11 passed".
  4. Resize to 375px; confirm the header wraps with no page-level horizontal scroll.
Review:
  - [x] the Scenarios tab lists the gold scenarios (name, user text, tools, components)
  - [x] "Run all" reports 11/11 passed, keylessly
  - [x] each scenario shows its actual tool sequence and components
  - [x] no page-level horizontal scroll at 375px (header wraps)
  - [x] no console errors
Clauses: P7, P8, HR-8, WV-3, WV-4, WV-6, WV-8
Features: 016
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/016-scenario-runner/checkpoint.png`

| Check | Result |
| --- | --- |
| Scenarios tab lists all 11 gold scenarios | pass |
| "Run all" → 11/11 passed (keyless; no API key, no spend) | pass |
| Per-scenario tools/components shown (e.g. `start_return` → tools `list_orders, start_return`, components `orders, return`) | pass |
| Header usable at 375px; `documentElement.scrollWidth == innerWidth` (no horizontal scroll) | pass |
| Console errors | 0 |

## Notes

- The runner calls `evals.runner.run_scenarios` — the same code the gate CLI runs —
  so browser and gate results cannot drift (SC-001).
- Each scenario runs on fresh in-memory/temp resources; the live session,
  storefront, memory, and budget are untouched.
- The run is keyless (scripted mock model); no DeepSeek call was made.
