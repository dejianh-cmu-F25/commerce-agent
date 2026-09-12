# Data Model: Observability

## Span (`app/core/types.py`)

| Field | Type | Notes |
| --- | --- | --- |
| `trace_id` | `str` | one per turn |
| `span_id` | `str` | unique |
| `parent_id` | `str \| None` | the turn span id, or `None` for the root |
| `name` | `str` | `turn` \| `llm` \| `tool` |
| `start_ms` | `float` | epoch milliseconds |
| `end_ms` | `float` | epoch milliseconds |
| `status` | `str` | `ok` \| `error` \| `budget` \| `max_turns` |
| `attributes` | `dict` | redacted, see below |

### Attributes by span

| Span | Attributes |
| --- | --- |
| `turn` | `session_id`, `reason`, `steps` |
| `llm` | `prompt_tokens`, `completion_tokens`, `cost_cny`, `tool_calls` |
| `tool` | `name`, `status`, `arguments` (truncated), `output` (truncated) |

## JSONL line

```json
{"trace_id":"…","span_id":"…","parent_id":null,"name":"turn","start_ms":1.0,"end_ms":2.0,"status":"ok","attributes":{"session_id":"…"}}
```

## TraceSummary (API)

| Field | Type |
| --- | --- |
| `trace_id` | `str` |
| `start_ms` | `float` |
| `duration_ms` | `float` |
| `span_count` | `int` |
| `status` | `str` |

## Config (`observability`, existing)

| Field | Default | Use |
| --- | --- | --- |
| `trace_enabled` | `true` | enable the JSONL tracer |
| `trace_file` | `./logs/traces.jsonl` | sink path |
| `trace_max_attr_len` | `500` (NEW) | redaction length |
