# Contract: Session Log

The session log is the source of truth for what the model sees (SL-1).

## Events (durable)

| Event | Fields |
| --- | --- |
| `UserMessage` | `text` |
| `AssistantMessage` | `text`, `tool_calls: list[ToolCall]` |
| `ToolResultEvent` | `call_id`, `name`, `content`, `status` (`ok`\|`blocked`\|`error`) |

## Projection

`derive_messages(session, system_prompt) -> list[Message]` is the **only** way to
build model messages. It emits a leading system message, then maps each event to
its message form.

## Invariant (SL-1)

`Agent.build_request(session)` re-derives the projection and compares it with the
messages it is about to send. Any mismatch raises `SL1Violation` and the turn
ends with an error event. In practice the loop has a single construction path, so
a mismatch signals a bug rather than bad data.

## Derived state

- `provenance`: the set of server-issued ids seen this session. Writes and renders
  accept only ids in this set (P4).
- `cart`: lines built from catalog data, never from model text.
