# Data Model: Browser Resume

## StoredSession (browser)

| Key | Value | Notes |
| --- | --- | --- |
| `commerce-agent.session` | `session_id` (string) | written on `SessionStarted`; cleared by New chat or a 404 |

## Server messages (`GET /sessions/{id}`)

```json
{
  "session_id": "…",
  "messages": [
    {"role": "user", "content": "…"},
    {"role": "assistant", "content": "…", "tool_calls": [{"id": "…", "name": "…", "arguments": "…"}]},
    {"role": "tool", "content": "…", "tool_call_id": "…", "name": "…"}
  ]
}
```

## Resume mapping

| Server role | UIMessage |
| --- | --- |
| `user` | `{ role: "user", parts: [{ type: "text", text: content }] }` |
| `assistant` | `{ role: "assistant", parts: [{ type: "text", text: content }] }` (empty text → message skipped) |
| `tool` | skipped |

Message `id`s are generated client-side (`crypto.randomUUID`).
