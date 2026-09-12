# Browser checkpoint: 001-agent-core

Constitution SR-4 / SR-5. Driven with Playwright MCP (Chrome, `--isolated`)
against the live app on real DeepSeek (`deepseek-flash`).

## Card

```
Checkpoint: 001 agent core
URL:    http://127.0.0.1:8000
Steps:
  1. Type "I need a tent under $250 for a weekend trip" and send.
  2. Expect a streamed reply that calls search_products and recommends a tent.
Review:
  - [x] assistant text streams into the page
  - [x] a search_products tool call is shown, with an [ok] result
  - [x] the recommendation respects the $250 budget
  - [x] the header budget updates from the UsageReported event
Clauses: WV-1..WV-5, SL-1, HR-12
Features: 001
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/001-agent-core/checkpoint.png`
- Observed: text streamed; `search_products` called twice (both `[ok]`);
  answer `2-Person Tent — $189 (in stock)`; header budget `¥0.0218 / ¥10.00`.

## Bug found and fixed during this checkpoint

The SSE client in `web/static/app.js` split the event stream on `\n\n`, but
`sse_starlette` separates events with `\r\n\r\n`. No event ever parsed, so the
page rendered nothing even though the model call succeeded and was billed
(`data/budget.json` grew). Fixed by normalizing CRLF to LF before splitting:

```js
buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
```

Re-ran the checkpoint after the fix; it passed.

## Known minor (non-blocking)

- `GET /favicon.ico` returns 404 — console noise only.
- Tool-call lines render inline with adjacent text rather than on their own
  lines (cosmetic; revisit under a later web feature).
