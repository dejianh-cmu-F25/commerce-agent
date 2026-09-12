# Contract: UI surface

Two contracts: the SSE events the client consumes, and the small backend
extension that lets a tool surface a UI component.

## 1. SSE event stream (`POST /chat`)

Unchanged from feature 001 except that `UIComponent` is now emitted in practice.
Framing: `sse_starlette`, events separated by CRLF; the client normalizes to LF.

| `type` | `data` fields | Client behavior |
| --- | --- | --- |
| `SessionStarted` | `session_id` | remember session |
| `TurnStart` | `turn_id` | status `submitted`; new agent message |
| `TextDelta` | `text` | append; status `streaming`; render markdown |
| `ToolCallStarted` | `name`, `arguments` | add a tool step (running) |
| `ToolResult` | `name`, `status`, `summary` | update the latest matching step |
| `UIComponent` | `component`, `payload` | dispatch to `componentRegistry` |
| `UsageReported` | `spent_cny`, `limit_cny`, `remaining_cny` | update budget meter |
| `BudgetExceeded` | `spent_cny`, `limit_cny` | inline notice |
| `ErrorEvent` | `message` | inline error + Retry |
| `TurnEnd` | `turn_id`, `reason` | status `ready`; enable Send |

Ordering guarantee (from 001): `TurnStart → (ToolCallStarted → ToolResult)* →
TextDelta* → TurnEnd`.

## 2. Backend extension: tool-declared UI component

`app/tools/registry.ToolResult` gains two optional fields:

```python
@dataclass
class ToolResult:
    content: str
    status: str = "ok"
    component: str | None = None  # NEW: registered component type
    payload: dict[str, Any] | None = None  # NEW: renderer payload
```

`Agent._execute_call` emits, after the `ToolResult` event:

```python
if result.component:
    await sink.emit(ev.UIComponent(component=result.component, payload=result.payload or {}))
```

Rules:
- The loop MUST NOT interpret `component`/`payload`; it only forwards them
  (keeps the loop generic, P2/P5).
- A tool that sets `component` MUST also provide a `payload` matching a renderer
  registered in `web/static/app.js` (WV-3). Unknown components fall back to a
  text notice in the generic renderer.
- `search_products` sets `component="products"` with
  `payload={"items": [{id, title, price, in_stock}, ...]}`.

## 3. Registered components (client)

| Component | Payload | Renderer |
| --- | --- | --- |
| `products` | `{items: Source[]}` | product/sources card (existing, now used) |
| *(unknown)* | any | generic `[ui] <name> (no renderer)` fallback |
