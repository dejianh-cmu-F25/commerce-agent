# Browser checkpoint: 003-react-web-ui

Constitution SR-4 / SR-5. Driven with Playwright against the FastAPI-served
build (real DeepSeek, `deepseek-flash`).

## Card

```
Checkpoint: 003 React web UI
URL:    http://127.0.0.1:8000
Steps:
  1. On load, confirm the empty state, suggestion buttons, and budget meter.
  2. Click a suggestion, then send.
  3. Confirm the reply renders as markdown, tool steps show a status, sources
     are listed, and the budget meter updates.
  4. Send again and press Stop mid-stream.
  5. Stop the server, send, confirm the error + Retry, restart, Retry.
  6. Resize to 375px and toggle the system theme.
Review:
  - [x] UI states (empty / submitted / streaming / success / error / disabled)
  - [x] assistant markdown rendered via AI Elements MessageResponse
  - [x] tool calls rendered as AI Elements Tool steps with a status
  - [x] grounding sources rendered via AI Elements Sources
  - [x] Stop and Retry via useChat
  - [x] layout fills the viewport; no horizontal scroll at 375px
  - [x] keyboard operable; streamed content in a live region
  - [x] theme follows the OS
  - [x] model markup sanitized (no XSS)
Clauses: WV-1, WV-3, WV-6..WV-9, P4, HR-12
Features: 003
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/003-react-web-ui/checkpoint.png`

| Check | Result |
| --- | --- |
| Empty state: 3 suggestions; budget `—` | pass |
| Suggestion seeds the composer; send works | pass |
| Markdown rendered (headings, list, bold) | pass |
| 2 `Tool` steps, both `Completed` | pass |
| `Sources` triggers ("Used 5 sources", "Used 1 sources") | pass |
| Budget meter `¥0.0438 / ¥10.00` | pass |
| Stop aborts; composer re-enabled | pass |
| Error "Failed to fetch" + Retry; Retry recovers | pass |
| Sanitize: no script, no `onerror`, no execution | pass |
| Layout: full height (`fullHeight: true`); no horizontal scroll at 375px | pass |
| Theme: light `oklch(1 0 0)` / dark `oklch(0.145 0 0)` | pass |
| Console errors | 0 |

## Notes

- The SPA is served by FastAPI from `web/static/app` (Vite build); `/chat`,
  `/healthz`, `/readyz`, `/budget` are unchanged.
- The backend event contract is unchanged; `frontend/src/lib/transport.ts`
  adapts the SSE stream to AI SDK UI message chunks.
- Bundle is large (Streamdown + shiki); lazy code-highlighting is a follow-up.

## Responsive fix (2026-09-13, `fix/003-responsive-layout`)

The first 003 build used a fixed 768px column and a top-aligned empty state, so
the layout did not scale with the window. Fixed per `docs/ui-conventions.md`:

- One responsive column shared by header, transcript, and composer
  (`max-w-3xl` → `lg:max-w-5xl` → `xl:max-w-6xl`), so they stay aligned.
- Empty state fills the transcript area and centers vertically.
- Suggestion row wraps instead of overflowing on narrow screens.

Measured (empty state, live resize):

| Viewport | body == window | h-overflow | empty h == transcript | column w | header/form aligned |
| --- | --- | --- | --- | --- | --- |
| 1920×1080 | yes | none | yes (898) | 1152 | yes |
| 1440×900 | yes | none | yes (718) | 1152 | yes |
| 1024×700 | yes | none | yes (518) | 992 | yes |
| 768×800 | yes | none | yes (618) | 738 | yes |
| 375×700 | yes | none | yes (518) | 345 | yes |
