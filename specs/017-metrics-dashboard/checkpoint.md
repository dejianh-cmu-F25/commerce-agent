# Browser checkpoint: 017-metrics-dashboard

Constitution SR-4 / SR-5. The Metrics view is a new browser surface, so a
checkpoint is recorded.

## Card

```
Checkpoint: 017 metrics dashboard
URL:    http://127.0.0.1:8000
Steps:
  1. Send a message (a real turn), then open the Metrics tab.
  2. Confirm latency-by-span, token tiles (incl. cache hits), cost, tools, and budget.
  3. Resize to 375px; confirm no page-level horizontal scroll.
Review:
  - [x] Metrics tab shows spans, tokens (cache hits), cost, tools, budget
  - [x] latency table has count/errors/avg/p95 per span type
  - [x] a new turn is reflected (span count and cache tokens increase)
  - [x] no page-level horizontal scroll at 375px
  - [x] no console errors
Clauses: OB-1, OB-3, OB-5, P3, P8, RD-1, WV-3, WV-6, WV-8
Features: 017
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/017-metrics-dashboard/checkpoint.png`

| Check | Result |
| --- | --- |
| Metrics tab renders (read-only, keyless) | pass |
| Tiles: spans 101, prompt 59,665, completion 5,186, cache 2,688 / 3,091, cost ¥0.0834, tools 28/0, budget ¥0.17 / ¥10.00 | pass |
| Latency by span: `llm` 48/1078.8ms, `tool` 28/0.2ms, `turn` 21/2467.2ms, `memory` 4/0.4ms | pass |
| A new turn added spans and cache-hit tokens (previously 0) | pass |
| No page-level horizontal scroll at 375px | pass |
| Console errors | 0 |

## Notes

- Bug found and fixed during this checkpoint: with the sixth tab, the header did
  not shrink at 375px (page overflowed by 22px). Added `min-w-0` so the tab group
  scrolls inside its own container; re-verified `documentElement.scrollWidth ==
  innerWidth == 375`. This is exactly what the checkpoint exists to catch (WV-8).
- Cache hit/miss tokens now appear on new LLM spans (FR-003); older spans predate
  the attribute and contribute 0.
- Metrics are read from `logs/traces.jsonl`; the view is read-only and needs no
  key.
