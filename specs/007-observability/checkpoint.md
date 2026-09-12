# Browser checkpoint: 007-observability

Constitution SR-4 / SR-5. The chat is user-visible and traces are the new
observability layer, so a checkpoint is recorded.

## Card

```
Checkpoint: 007 observability
URL:    http://127.0.0.1:8000
Steps:
  1. Send a message.
  2. Confirm the chat is unchanged.
  3. GET /traces and GET /traces/{trace_id}.
Review:
  - [x] chat parity (tool step, sources)
  - [x] each turn writes turn/llm/tool spans sharing a trace_id
  - [x] llm spans carry tokens + cost; tool spans carry name/status
  - [x] traces are readable via the API (404 unknown)
Clauses: SL-2, OB-1, OB-2, OB-3, OB-5, PB-1, PB-2
Features: 007
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/007-observability/checkpoint.png`

| Check | Result |
| --- | --- |
| Chat parity (tool step, sources); 0 console errors | pass |
| `GET /traces` lists the trace (`span_count`, `duration_ms`, `status`) | pass |
| `GET /traces/{id}` → spans `turn, llm, tool, llm, tool, llm` | pass |
| `llm` span attributes: `prompt_tokens`, `completion_tokens`, `cost_cny` | pass |
| `turn` span attributes: `session_id`, `reason` | pass |
| Unknown trace id → 404 | pass |
| `logs/traces.jsonl` written (one JSON object per span) | pass |

## Notes

- Tracing is configurable (`observability.trace_enabled`, `trace_file`,
  `trace_max_attr_len`); `NullTracer` is used when disabled.
- Inputs/outputs are truncated before writing (OB-5).
- The web Trace Viewer (OB-4) is a follow-up; this feature exposes the read API.
