# Data Model: Web Experience

Client-side view model. Nothing here is persisted; it is derived from the SSE
event stream (SL-1: the session log remains the source of truth).

## TurnStatus

`idle | submitted | streaming | ready | error`

- `idle` — no turn in flight.
- `submitted` — message sent, no token yet.
- `streaming` — first token received, stream open.
- `ready` — turn ended normally (or aborted by Stop).
- `error` — `ErrorEvent` or network failure.

## Message

| Field | Type | Notes |
| --- | --- | --- |
| `role` | `"user" \| "agent"` | |
| `text` | `string` | Raw text (agent); markdown-rendered on display |
| `steps` | `ToolStep[]` | Agent messages only |
| `sources` | `Source[]` | Agent messages only; from `UIComponent(products)` |
| `cost` | `number?` | Latest turn cost, if reported |

## ToolStep

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `string` | e.g. `search_products` |
| `arguments` | `object` | From `ToolCallStarted` |
| `status` | `"running" \| "ok" \| "error" \| "blocked"` | running until `ToolResult` |
| `summary` | `string?` | From `ToolResult.summary` |
| `expanded` | `boolean` | UI-only disclosure state |

## Source

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `string` | Server-issued product id (P4) |
| `title` | `string` | |
| `price` | `number` | |
| `in_stock` | `boolean` | |

## Suggestion

| Field | Type | Notes |
| --- | --- | --- |
| `label` | `string` | Chip text |
| `prompt` | `string` | Fills the input when clicked (no auto-send) |

Static list in the client for the empty state.

## BudgetMeter

| Field | Type | Notes |
| --- | --- | --- |
| `spent` | `number` | From `UsageReported.spent_cny` |
| `limit` | `number` | From `UsageReported.limit_cny` |
| `lastTurnCost` | `number?` | Delta since the turn started |

## Event → view-model mapping

| Event | Effect |
| --- | --- |
| `SessionStarted` | store `session_id` |
| `TurnStart` | status `submitted`; open agent message |
| `TextDelta` | append text; status `streaming` |
| `ToolCallStarted` | push `ToolStep{status: running}` |
| `ToolResult` | set step status/summary |
| `UIComponent` (`products`) | set message `sources`; render products |
| `UsageReported` | update `BudgetMeter` |
| `BudgetExceeded` | inline notice; status `error` |
| `ErrorEvent` | inline error; status `error` |
| `TurnEnd` | status `ready`; enable Send; hide Stop |
