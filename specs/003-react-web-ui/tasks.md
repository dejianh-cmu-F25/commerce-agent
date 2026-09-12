# Tasks: React Web UI

**Feature**: `003-react-web-ui` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 0 — Spike (done)

- [x] T001 Scaffold `frontend/` (Vite + React 19 + TS + Tailwind v4)
- [x] T002 `shadcn init` + add AI Elements (message, conversation, prompt-input, tool, sources, suggestion)
- [x] T003 Custom `ChatTransport` (`src/lib/transport.ts`) — SSE → `UIMessageChunk`
- [x] T004 Verify a real DeepSeek turn renders under Vite (spike passed)

## Phase 1 — Feature parity

- [x] T005 `src/components/app/budget-meter.tsx` from `data-budget`
- [x] T006 `src/components/app/sources.tsx` from `data-sources` (AI Elements `Sources`)
- [x] T007 `src/components/app/tool-step.tsx` wrapper around AI Elements `Tool`
- [x] T008 `App.tsx`: render text/tool/data parts; suggestions empty state
- [x] T009 Stop + Retry via `useChat` status; Esc to stop
- [x] T010 Full-viewport layout; header/composer full width; no horizontal scroll at 375px
- [x] T011 Theme (shadcn tokens + `prefers-color-scheme`), a11y (focus, live region)

## Phase 2 — Delivery

- [x] T012 `web/main.py`: serve the built SPA at `/`; keep API routes; cache headers for hashed assets
- [x] T013 Remove the vanilla surface (`web/static/app.js`, `index.html`, `styles.css`, `vendor/`)
- [x] T014 `Dockerfile`: multi-stage (node build → python runtime)
- [x] T015 `.gitignore`: `frontend/node_modules/`, `web/static/app/`
- [x] T016 `ci.yml`: frontend job (`npm ci`, `eslint`, `tsc --noEmit`, `vitest`, `npm run build`)
- [x] T017 Agent Note: framework decision and alternatives (DR-1)
- [x] T018 Update `docs/architecture.md` (frontend row)

## Phase 3 — Verification

- [x] T019 `vitest` transport mapping tests (incl. sanitization assertion)
- [x] T020 Python checks unchanged: `ruff`, `pyright`, `pytest`, `spec_review`
- [x] T021 Browser checkpoint (Playwright) + `checkpoint.png` + `checkpoint.md`
- [x] T022 Commit and open the PR

## Dependencies

- T005–T007 precede T008.
- T012–T013 follow T008–T011.
- T019–T022 follow all implementation.
