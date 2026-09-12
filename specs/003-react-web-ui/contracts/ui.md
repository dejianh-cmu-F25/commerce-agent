# Contract: React UI transport

The backend event contract is **unchanged**. This feature adds a client-side
adapter (`frontend/src/lib/transport.ts`) that turns the `POST /chat` SSE stream
into AI SDK `UIMessageChunk`s consumed by `useChat` and rendered by AI Elements.

## 1. Backend stream (unchanged, from 001/002)

`POST /chat` → `text/event-stream` (`sse_starlette`, CRLF-separated). Events:

`SessionStarted · TurnStart · TextDelta · ToolCallStarted · ToolResult ·
UIComponent · CartUpdate · UsageReported · BudgetExceeded · ErrorEvent ·
TurnEnd`

## 2. Event → UIMessageChunk mapping

| Backend event | AI SDK chunk(s) |
| --- | --- |
| `SessionStarted` | *(none; transport stores `session_id`)* |
| `TurnStart` | `{ type: "start" }` |
| `TextDelta` | `text-start` (once) then `text-delta` |
| `ToolCallStarted` | `tool-input-start` + `tool-input-available` |
| `ToolResult` | `tool-output-available` (`{status, summary}`) |
| `UIComponent` (`products`) | `data-sources` (`{items}`) |
| `UsageReported` | `data-budget` (`{spent_cny, limit_cny, remaining_cny}`) |
| `BudgetExceeded` | `error` |
| `ErrorEvent` | `error` |
| `TurnEnd` | `text-end` (if open) + `finish` |

Rules:
- Tool calls are matched to results by name using a per-name stack of
  `toolCallId`s (started before results, as the loop guarantees).
- Custom data parts are declared in `AgentDataTypes` (`sources`, `budget`).
- The transport only reads the stream; it never writes session state (SL-1).

## 3. Rendering (AI Elements)

| Message part | Component |
| --- | --- |
| `text` | `Message` / `MessageContent` / `MessageResponse` (Streamdown) |
| `tool-*` | `Tool` / `ToolHeader` / `ToolContent` / `ToolInput` / `ToolOutput` |
| `data-sources` | `Sources` / `SourcesTrigger` / `SourcesContent` / `Source` |
| `data-budget` | app `BudgetMeter` |

## 4. Status model

`useChat().status` (`ready | submitted | streaming | error`) drives the composer
(`PromptInputSubmit`), Stop, and Retry.

## 5. Rendering safety (WV-9)

`MessageResponse` renders model markdown; a test asserts that injected
`<script>`, `onerror`, and `javascript:` URLs do not survive/execute.
