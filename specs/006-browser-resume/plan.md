# Implementation Plan: Browser Resume

**Branch**: `006-browser-resume` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-browser-resume/spec.md`

## Summary

Persist the `session_id` in browser storage, and on load fetch
`GET /sessions/{id}` (from 005) to rehydrate the transcript via `useChat`'s
`setMessages`. Add a New chat action. Text-only history (tool steps are not
reconstructed).

## Technical Context

**Language/Version**: TypeScript / React 19 (Vite), no backend change

**Primary Dependencies**: `@ai-sdk/react` `useChat` (`setMessages`), browser
`localStorage`

**Storage**: browser `localStorage`; server SQLite (005)

**Testing**: `vitest` (rehydration mapping, storage helpers); Playwright checkpoint

**Target Platform**: modern browsers

**Project Type**: web service (frontend)

**Performance Goals**: one history request per load

**Constraints**: no new dependencies; failures degrade to a fresh session

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| WV-1 / WV-6 | spec has `## Web Acceptance` + `## UI States` | PASS |
| WV-2 / WV-5 | demonstrable in the browser; uses the 005 endpoint | PASS |
| SL-1 | resume reads the server log; the client never builds model context | PASS |
| P6 / HR-9 | no new dependencies; small helpers | PASS |
| P8 | works keyless (resume is a read) | PASS |
| RD-1 | history-load failure degrades to a fresh session | PASS |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-browser-resume/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/resume.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
frontend/src/
├── lib/
│   ├── transport.ts     # persist/read/clear the session id
│   ├── resume.ts        # server messages -> UIMessage[]
│   └── resume.test.ts   # vitest for the mapping
└── App.tsx              # rehydrate on load; New chat action
```

**Structure Decision**: Keep the mapping and storage in `src/lib` so they are
unit-testable without React; `App.tsx` wires them to `useChat`.

## Complexity Tracking

> No constitution violations; nothing to justify.
