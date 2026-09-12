# Implementation Plan: Web Trace Viewer

**Branch**: `008-trace-viewer` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-trace-viewer/spec.md`

## Summary

Add a client-side Chat/Traces toggle. The Traces view lists recent traces from
`GET /traces` (007) and renders a selected trace's span timeline from
`GET /traces/{id}`, with durations, status, and attributes. No backend change.

## Technical Context

**Language/Version**: TypeScript / React 19 (Vite)

**Primary Dependencies**: existing (fetch, Tailwind, AI Elements primitives)

**Storage**: none (reads the 007 API)

**Testing**: `vitest` (duration formatting + span tree helpers); Playwright checkpoint

**Target Platform**: modern browsers

**Project Type**: web service (frontend)

**Performance Goals**: one list request on open; one detail request per select

**Constraints**: no new dependencies; chat must be unaffected

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| WV-1 / WV-6 | spec has `## Web Acceptance` + `## UI States` | PASS |
| WV-2 / WV-5 | browser-demonstrable; renders the 007 API | PASS |
| WV-7 / WV-8 | responsive + theme via the existing shell | PASS |
| SL-1 | read-only view of the server log's traces | PASS |
| P6 / HR-9 | no new dependencies; small helpers | PASS |
| RD-1 | empty/error states, Refresh | PASS |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-trace-viewer/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/viewer.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
frontend/src/
├── lib/
│   ├── traces.ts          # types, fetch helpers, formatDuration, buildSpanTree
│   └── traces.test.ts     # vitest
├── components/app/
│   └── trace-viewer.tsx   # list + timeline
└── App.tsx                # Chat/Traces toggle; render the viewer
```

## Complexity Tracking

> No constitution violations; nothing to justify.
