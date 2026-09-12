# Research: Web Trace Viewer

## D1. Navigation

**Decision**: a client-side view toggle in the header (`chat` | `traces`) held in
React state. No router.

**Rationale**: the app is a single page; adding a router is unnecessary (P6).

**Alternatives considered**: hash routing (rejected: extra complexity, not
needed); a separate page (rejected: no router).

## D2. Data fetching

**Decision**: plain `fetch` in the viewer, with `loading`/`error`/`empty` states.
A Refresh button re-runs the list request.

**Rationale**: two endpoints, no caching needs; keeps the bundle small.

**Alternatives considered**: a data library (rejected: dependency for two GETs).

## D3. Timeline layout

**Decision**: order spans by `start_ms`; indent by `parent_id` depth; show name,
duration (`end_ms - start_ms`), status badge, and attributes as key/value rows.

**Rationale**: reads like the turn/step/tool structure; matches OB-4.

## D4. Pure helpers for testability

**Decision**: `formatDuration(ms)` and `buildSpanTree(spans)` live in
`lib/traces.ts` and are unit-tested with vitest (no DOM).

**Rationale**: the interesting logic is testable without React.
