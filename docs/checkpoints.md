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
| 002 web experience | 002 | UI states, markdown, tool steps, sources, stop/retry, a11y, theme | PASS (2026-09-13) |
| 003 React web UI | 003 | React + AI Elements parity, full-viewport layout, theme, sanitization | PASS (2026-09-13) |
| 004 storefront backend | 004 | catalog reads from the configured backend; parity; /readyz | PASS (2026-09-13) |
| 005 session persistence | 005 | session survives restart; GET /sessions/{id}; parity | PASS (2026-09-13) |
| 006 browser resume | 006 | reload restores the transcript; same session continues; New chat | PASS (2026-09-13) |
| 007 observability | 007 | turn/llm/tool spans with trace_id; GET /traces; parity | PASS (2026-09-13) |
| 008 trace viewer | 008 | Chat/Traces toggle; trace list + span timeline; chat preserved | PASS (2026-09-13) |
| 009 cart & checkout | 009 | grounded add-to-cart; cart card; render_checkout (no charge) | PASS (2026-09-13) |
| 010 merchant agent | 010 | inventory; staged price change; human approval applies it (P3) | PASS (2026-09-13) |
| 011 evaluation | 011 | keyless replay of gold scenarios in the local gate | N/A (no browser surface) |
| 012 knowledge retrieval | 012 | search_knowledge; answer grounded in policy docs | PASS (2026-09-13) |
| 013 customer memory | 013 | durable facts stored; recalled in a new chat; forget | PASS (2026-09-13) |
| 014 post-purchase care | 014 | order status cards; in-window return; out-of-window refusal | PASS (2026-09-13) |

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

### 002 web experience — 2026-09-13

- Driver: Playwright (Chrome, isolated), real DeepSeek (`deepseek-flash`).
- Result: PASS. Verified empty state + suggestion chips, markdown rendering,
  tool steps with status, sources card, budget meter, Stop, error + Retry,
  sanitization (no XSS), 375px with no horizontal scroll, and light/dark theme.
- Card and details: `specs/002-web-experience/checkpoint.md`.
- Screenshot: `specs/002-web-experience/checkpoint.png`.
- Fixed the two 001 minor items: favicon added (`/static/favicon.svg`, no more
  404) and tool calls now render as their own steps.
- Backend seam: `ToolResult` gained optional `component`/`payload`; the loop
  forwards a tool-declared `UIComponent` (generic; `search_products` declares
  `products`).

### 003 React web UI — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. React 19 + AI Elements rebuilt the surface with full parity
  (markdown, `Tool` steps, `Sources`, budget meter, Stop, error + Retry) plus a
  full-viewport layout and system-theme following.
- Card and details: `specs/003-react-web-ui/checkpoint.md`.
- Screenshot: `specs/003-react-web-ui/checkpoint.png`.
- Architecture: a custom `ChatTransport` adapts the existing SSE stream to AI
  SDK `UIMessageChunk`; the backend event contract is unchanged. See the Agent
  Note `docs/notes/implemented/architecture/2026-09-13-react-ai-elements-frontend.md`.

### 004 storefront backend — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. `search_products` now reads from the configured storefront
  (`sqlite` by default); behavior is unchanged and sources still render.
- Card and details: `specs/004-storefront-backend/checkpoint.md`.
- Screenshot: `specs/004-storefront-backend/checkpoint.png`.
- `/readyz` reports the provider; seeding is idempotent (count stays 5 after
  restart).

### 005 session persistence — 2026-09-13

- Driver: Playwright + API checks, real DeepSeek.
- Result: PASS. The chat is unchanged; the session is persisted and survives a
  restart (`GET /sessions/{id}` returns the derived messages).
- Card and details: `specs/005-session-persistence/checkpoint.md`.
- Screenshot: `specs/005-session-persistence/checkpoint.png`.
- The web app is now built via a factory (`uvicorn web.main:create_app --factory`);
  Docker and `serve.sh` use the same command.

### 006 browser resume — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. The session id is stored in the browser; a reload restores the
  transcript from `GET /sessions/{id}` and the next message continues the same
  session. New chat clears it; a stale id is cleared gracefully.
- Card and details: `specs/006-browser-resume/checkpoint.md`.
- Screenshot: `specs/006-browser-resume/checkpoint.png`.
- History is text-only (tool steps are not reconstructed).

### 007 observability — 2026-09-13

- Driver: Playwright + API checks, real DeepSeek.
- Result: PASS. The chat is unchanged; each turn writes `turn`/`llm`/`tool` spans
  to `logs/traces.jsonl` sharing a `trace_id`, readable via `GET /traces`.
- Card and details: `specs/007-observability/checkpoint.md`.
- Screenshot: `specs/007-observability/checkpoint.png`.
- The web Trace Viewer (OB-4) is a follow-up.

### 008 trace viewer — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. A Chat/Traces toggle lists recent traces and renders a selected
  trace's `turn`/`llm`/`tool` timeline with durations, status, and attributes;
  switching back preserves the chat.
- Card and details: `specs/008-trace-viewer/checkpoint.md`.
- Screenshot: `specs/008-trace-viewer/checkpoint.png`.

### 009 cart and checkout — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. A grounded add renders a cart card; `render_checkout` renders a
  summary and states that nothing is charged (P3).
- Card and details: `specs/009-cart-checkout/checkpoint.md`.
- Screenshot: `specs/009-cart-checkout/checkpoint.png`.

### 010 merchant agent — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. The operator agent lists inventory and stages a price change; a
  human approves it in the Merchant view and only then does the product update
  (P3).
- Card and details: `specs/010-merchant-agent/checkpoint.md`.
- Screenshot: `specs/010-merchant-agent/checkpoint.png`.

### 011 evaluation — 2026-09-13

- No browser surface: the harness replays gold scenarios over the real loop/tools
  keylessly and runs in the local gate (`scripts/ci.sh`). Report: `evals/run.py`
  (5/5 scenarios pass). WV-5 permits backend-only features with a recorded reason.

### 012 knowledge retrieval — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. The agent called `search_knowledge` and answered the return
  policy from the grounded document (30-day window, refund process).
- Card and details: `specs/012-knowledge-retrieval/checkpoint.md`.
- Screenshot: `specs/012-knowledge-retrieval/checkpoint.png`.

### 013 customer memory — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. Stating "I usually wear size M and I'm allergic to wool" stored
  two facts (Profile / Constraint); a **new chat** answered "You wear size M and
  you avoid wool." from memory; the Memory view listed the facts and forgetting
  one removed it. `memory` spans recorded `extract` (stored=2) and `recall`
  (recalled=2).
- Card and details: `specs/013-customer-memory/checkpoint.md`.
- Screenshot: `specs/013-customer-memory/checkpoint.png`.

### 014 post-purchase care — 2026-09-13

- Driver: Playwright against the FastAPI-served SPA, real DeepSeek.
- Result: PASS. "Where is my order?" rendered an orders list and a grounded order
  detail card; returning the tent on the in-window order O-1001 rendered a
  "Return requested" card ("No refund is issued yet"); returning the backpack on
  the out-of-window order O-1002 was refused with the window reason and no return
  card.
- Card and details: `specs/014-post-purchase/checkpoint.md`.
- Screenshot: `specs/014-post-purchase/checkpoint.png`.
