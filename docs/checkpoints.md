# Checkpoints

A checkpoint is a moment where the agent starts the app, opens the page, and
hands the reviewer a card describing what to look at (constitution SR-4, SR-5).

## Trigger

A feature triggers a checkpoint when its `spec.md` has a non-empty
`## Web Acceptance` section — that is, when it introduces or changes
browser-visible content.

Backend-only features still expose a web entry where practical (WV-5). A feature
with no browser surface at all records why in its review.

## Running a checkpoint

```sh
./scripts/serve.sh          # real DeepSeek, opens the browser
NO_OPEN=1 ./scripts/serve.sh   # headless
```

Endpoints: `/` chat, `/budget`, `/healthz`, `/readyz`.

## Review card template

```
Checkpoint: <feature id and name>
URL:    http://localhost:8000
Steps:
  1. <action>
  2. <expected result>
Review:
  - [ ] <clause or behavior to verify>
  - [ ] <clause or behavior to verify>
Clauses: <constitution clauses under review>
Features: <feature ids>
```

## Checkpoint log

| Checkpoint | Features | What to review | Status |
| --- | --- | --- | --- |
| 001 agent core | 001 | chat, SSE streaming, tool call, budget, health | PASS (2026-09-13) |

### 001 agent core — 2026-09-13

- Driver: Playwright MCP (Chrome, `--isolated`), real DeepSeek (`deepseek-flash`).
- Scenario: `I need a tent under $250 for a weekend trip`.
- Result: PASS. Agent streamed text, called `search_products` (twice, both `[ok]`),
  answered with `2-Person Tent — $189 (in stock)`, and the header budget updated to
  `¥0.0218 / ¥10.00`.
- Card and details: `specs/001-agent-core/checkpoint.md`.
- Screenshot: `specs/001-agent-core/checkpoint.png`.
- Bug found and fixed during this checkpoint: the SSE client split events on `\n\n`
  while `sse_starlette` emits `\r\n\r\n`, so no event ever parsed and the UI rendered
  nothing (spend still occurred). Fixed in `web/static/app.js` by normalizing CRLF to LF
  before splitting. Re-run after the fix passed.
- Known minor (non-blocking): `/favicon.ico` returns 404 (console noise only);
  tool-call lines render inline with adjacent text instead of on their own lines.
