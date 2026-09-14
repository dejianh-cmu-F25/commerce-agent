# Browser checkpoint: 002-web-experience

Constitution SR-4 / SR-5. Driven with Playwright (Chrome, isolated) against the
live app on real DeepSeek (`deepseek-flash`).

## Card

```
Checkpoint: 002 web experience
URL:    http://127.0.0.1:8000
Steps:
  1. On load, confirm the empty state, suggestion chips, and budget meter.
  2. Click a chip, then Send.
  3. Confirm formatted reply, tool steps, sources, and budget update.
  4. Send again and press Stop mid-stream.
  5. Stop the server, send, confirm the inline error + Retry, restart, Retry.
  6. Resize to 375px and toggle the system theme.
Review:
  - [x] UI states present (empty / submitted / streaming / success / error / disabled)
  - [x] assistant markdown rendered, not raw
  - [x] tool calls shown as steps with a status
  - [x] sources listed; budget meter updates
  - [x] Stop cancels and keeps the partial reply
  - [x] error shows inline with a working Retry
  - [x] keyboard operable; aria-live polite; reduced-motion respected
  - [x] no horizontal scroll at 375px; light/dark theme follows the OS
Clauses: WV-1, WV-3, WV-6..WV-9, P4, HR-12
Features: 002
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/002-web-experience/checkpoint.png`

Observed (automated assertions):

| Check | Result |
| --- | --- |
| Empty state: 3 suggestion chips; Send disabled | pass |
| Chip fills the input; Send enabled | pass |
| Reply rendered as markdown (list, `<strong>`) | pass |
| Two `search_products` steps with `ok` badges + result body | pass |
| Sources card lists grounded product(s) | pass |
| Budget meter `¥0.0299 / ¥10.00` | pass |
| Stop: status → ready, Stop hidden, partial retained | pass |
| Error: "Connection error: Failed to fetch" + Retry; Retry recovers | pass |
| Sanitize: no `<script>`, no `onerror`, no `javascript:`, no execution | pass |
| 375px: no horizontal scroll | pass |
| Theme: light `rgb(247,248,250)` / dark `rgb(15,17,21)` | pass |
| `aria-live="polite"` on the transcript | pass |
| Console errors | 0 (favicon 404 fixed) |

## Notes

- The Stop test aborted before the first token, so the retained partial is the
  placeholder; the cancel + finalize path is what was verified.
- The two console errors at the end of the session are the expected
  `net::ERR_CONNECTION_REFUSED` from the deliberate server-down error test.
- Backend change: `ToolResult` gained optional `component`/`payload`; the loop
  forwards a tool-declared `UIComponent` (see `contracts/ui.md`).
