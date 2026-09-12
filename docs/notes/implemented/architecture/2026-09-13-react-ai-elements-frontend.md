# Agent Note: React + Vercel AI Elements frontend

Status: implemented (2026-09-13)

## Problem

Feature 002 built the browser surface in vanilla JS with a small component
registry. It worked, but the UI was hand-rolled, and the requested stack is
Vercel AI Elements (a React component registry built on shadcn/ui + Tailwind).
Using AI Elements means introducing React and a build toolchain, which P6
(simplicity) and HR-9 (minimal scaffolding) require us to justify. We also had a
layout gap (the app did not fill the viewport) and a heavy hand-written SSE
client to maintain.

## Decision

Rebuild the web surface as a **React 19 + Vite + TypeScript + Tailwind v4 +
shadcn/ui + AI Elements** app under `frontend/`, and drive it with `useChat`
from `@ai-sdk/react` over a **custom `ChatTransport`** that adapts the existing
`POST /chat` SSE stream to AI SDK UI message chunks. The backend event contract
is unchanged; the harness and session log are untouched (SL-1). FastAPI serves
the built SPA (`web/static/app`) so one container runs everything (DP-1). The
build runs in CI and in a multi-stage Docker image; `node_modules/` and build
output are not committed.

Generated registry components (AI Elements, shadcn/ui) are vendored and excluded
from strict typechecking, because the registry versions drifted (Radix→BaseUI)
from what the components assume.

## Alternatives considered

- **Keep the vanilla UI (002).** Rejected: it cannot use AI Elements, and the
  request was explicitly to adopt them.
- **Next.js (App Router), as AI Elements documents.** Rejected: our backend is
  Python/FastAPI; Next would add a second server and SSR we do not need. A Vite
  SPA is sufficient and was validated by a spike.
- **Add an AI SDK stream protocol endpoint in Python and use the default
  transport.** Rejected: it would change the backend event contract and duplicate
  the harness's event mapping. A client-side transport keeps the harness stable.
- **Use AI Elements purely as presentational components without AI SDK.**
  Rejected: we would re-implement `useChat`'s status/stop/regenerate by hand, for
  no benefit.
- **Load markdown/UI libraries from a CDN.** Rejected: breaks offline/container
  reproducibility (P8).

## Consequences

- The frontend now has a Node toolchain; CI gains a `frontend` job and the Docker
  image gains a Node build stage. `package-lock.json` is committed.
- The backend is unchanged; `web/main.py` only serves the built SPA and keeps the
  API routes.
- AI Elements gives us `Conversation`, `Message`/`Response` (Streamdown),
  `PromptInput`, `Tool`, and `Sources`; our app adds a budget meter and wiring.
- The main JS bundle is large (Streamdown + shiki). This is acceptable for the
  demo; lazy-loading code highlighting is a follow-up.
- Registry components are vendored; re-running the AI Elements CLI may overwrite
  them and reintroduce type drift, so updates should be deliberate.
