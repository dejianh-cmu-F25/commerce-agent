# Data Model: Web Trace Viewer

## TraceSummary (from `GET /traces`)

| Field | Type |
| --- | --- |
| `trace_id` | `string` |
| `start_ms` | `number` |
| `duration_ms` | `number` |
| `span_count` | `number` |
| `status` | `"ok" \| "error"` |

## Span (from `GET /traces/{trace_id}`)

| Field | Type |
| --- | --- |
| `trace_id` | `string` |
| `span_id` | `string` |
| `parent_id` | `string \| null` |
| `name` | `"turn" \| "llm" \| "tool"` |
| `start_ms` | `number` |
| `end_ms` | `number` |
| `status` | `string` |
| `attributes` | `Record<string, unknown>` |

## View model

- **SpanNode**: `{ span: Span; depth: number; children: SpanNode[] }`, built by
  `buildSpanTree(spans)` — roots have `parent_id === null` (or an unknown parent).
- **Duration**: `end_ms - start_ms`, formatted by `formatDuration` (`12 ms`,
  `1.2 s`).

## UI state

| Field | Type |
| --- | --- |
| `view` | `"chat" \| "traces"` |
| `traces` | `TraceSummary[]` |
| `selectedTraceId` | `string \| null` |
| `spans` | `Span[]` |
| `loading` / `error` | `boolean` / `string \| null` |
