# Implementation Plan: React Web UI

**Branch**: `003-react-web-ui` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-react-web-ui/spec.md`

## Summary

Replace the vanilla web surface with a React 19 + Vite + Tailwind v4 app built
from Vercel AI Elements (shadcn/ui), driven by `useChat` over a **custom
`ChatTransport`** that adapts the existing `POST /chat` SSE stream to AI SDK UI
message chunks. The backend event contract is unchanged. FastAPI serves the
built SPA. Feature parity with 002 plus a full-viewport layout.

Validated by a Phase 0 spike: AI Elements renders under Vite (no Next.js
dependency), the transport drives a real DeepSeek turn, markdown renders, zero
console errors.

## Technical Context

**Language/Version**: Python 3.13 (backend, unchanged) + TypeScript / React 19
(frontend, Vite build)

**Primary Dependencies**: `react`, `react-dom`, `ai` (AI SDK v7), `@ai-sdk/react`
(`useChat`), `tailwindcss` v4, `shadcn/ui`, AI Elements components, `streamdown`
(via `MessageResponse`), `lucide-react`

**Storage**: N/A (frontend only; session state stays server-side)

**Testing**: `vitest` (transport mapping), `eslint`, `tsc --noEmit`,
`npm run build`; existing `pytest`; Playwright browser checkpoint

**Target Platform**: modern desktop and mobile browsers (≥ 375px)

**Project Type**: web service with a built SPA frontend

**Performance Goals**: first token unchanged; interaction ≤ 200ms; acceptable
initial bundle (lazy-load code highlighting if needed)

**Constraints**: no backend event changes; build in CI/Docker; no committed
`node_modules`/dist; sanitized rendering (WV-9)

**Scale/Scope**: one surface; ~1 app component + transport + generated
components

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P6 / HR-9 (simplicity, minimal scaffolding) | framework justified by AI Elements; Agent Note recorded | PASS (note required) |
| P8 / DP-4 (reproducible) | `package-lock.json` committed; build in Docker/CI | PASS |
| WV-1 / WV-6 | spec has `## Web Acceptance` + `## UI States` | PASS |
| WV-3 (component registry) | AI Elements + our Sources/budget components | PASS |
| WV-7 / WV-8 | a11y + theme specified and tested | PASS |
| WV-9 (rendering safety) | Streamdown + sanitized links; test asserts | PASS |
| SL-1 (log is truth) | backend unchanged; transport is read-only | PASS |
| P4 / HR-12 | sources + budget from events | PASS |
| DP-5 / CI | new frontend job + Docker node stage | PASS |

Complexity introduced (Node toolchain) is justified in the Agent Note.

## Project Structure

### Documentation (this feature)

```text
specs/003-react-web-ui/
├── plan.md
├── contracts/ui.md          # transport mapping + backend contract (unchanged)
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
frontend/
├── package.json / package-lock.json
├── vite.config.ts           # dev proxy → :8000; build.outDir = ../web/static/app
├── tsconfig.json / eslint.config.js / components.json
└── src/
    ├── main.tsx / App.tsx
    ├── index.css            # Tailwind v4 + shadcn theme tokens
    ├── lib/transport.ts     # SSE → UIMessageChunk (tested)
    ├── lib/transport.test.ts
    ├── components/ai-elements/*   # generated (vendored)
    ├── components/ui/*            # generated (vendored)
    └── components/app/*           # budget meter, sources, tool wrapper

web/
├── main.py                  # serve SPA at / ; keep /chat,/healthz,/readyz,/budget
└── static/app/              # Vite build output (gitignored)
```

**Structure Decision**: A separate `frontend/` app keeps the Python harness
untouched and the build isolated. FastAPI serves the built assets so a single
container runs the whole demo (DP-1).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Node build toolchain (P6/HR-9) | The requested AI Elements stack requires React + Tailwind + a bundler | Hand-rolled vanilla UI (002) cannot use AI Elements; explicitly superseded by this feature |
