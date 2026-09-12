# Contract: Trace Viewer

## API consumed (from 007)

- `GET /traces?limit=50` → `{ "traces": TraceSummary[] }` (newest first).
- `GET /traces/{trace_id}` → `{ "trace_id": "...", "spans": Span[] }` or 404.

The viewer only reads; it never writes.

## Helpers (`frontend/src/lib/traces.ts`)

```ts
formatDuration(ms: number): string          // "12 ms" | "1.2 s"
buildSpanTree(spans: Span[]): SpanNode[]     // ordered by start_ms, indented by parent_id
listTraces(limit?: number): Promise<TraceSummary[]>
getTrace(traceId: string): Promise<Span[]>
```

- `buildSpanTree` treats a span whose `parent_id` is `null` **or unknown** as a
  root (never drops a span).
- `formatDuration` uses ms below 1s and one decimal of seconds above.

## UI (`frontend/src/components/app/trace-viewer.tsx`)

- Props: none (self-contained; fetches on mount).
- States: loading, empty, error, list, detail.
- Actions: Refresh (reload list), Select (load spans).

## Toggle (`frontend/src/App.tsx`)

- `view: "chat" | "traces"` in state; header buttons switch it.
- The Chat view (transcript + composer) is preserved when switching away and back.
