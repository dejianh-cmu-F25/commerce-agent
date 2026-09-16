# Browser checkpoint: 025-eval-report-view

Constitution SR-4 / SR-5. The Report view is a new browser surface, so a
checkpoint is recorded.

## Card

```
Checkpoint: 025 eval report view
URL:    http://127.0.0.1:8000
Steps:
  1. Open the Report tab.
  2. Confirm the report renders (headings + tables).
  3. Resize to 375px; confirm no page-level horizontal scroll.
Review:
  - [x] the Report tab renders evals/report.md
  - [x] tables render (retrieval, ablation, reliability, process, judge)
  - [x] the real-model section shows model/seeds/command
  - [x] no page-level horizontal scroll at 375px
  - [x] no console errors
Clauses: WV-1, WV-6, WV-8, WV-9
Features: 025
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/025-eval-report-view/checkpoint.png`

| Check | Result |
| --- | --- |
| `GET /report` returns the committed markdown (2,406 chars) | pass |
| Report view renders headings and GFM tables | pass |
| Sections present: retrieval, ablation, real reliability/process/judge | pass |
| `documentElement.scrollWidth == innerWidth` at 375px | pass |
| Console errors | 0 |

## Notes

- The view is read-only; it renders the committed `evals/report.md` through the
  sanitizing `MessageResponse`/Streamdown renderer (WV-9).
- A missing report shows the generating command instead of an error.
- The report records the model, seeds, and command, so the numbers are
  attributable.
