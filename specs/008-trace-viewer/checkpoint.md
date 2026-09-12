# Browser checkpoint: 008-trace-viewer

Constitution SR-4 / SR-5. The viewer is user-visible, so a checkpoint is recorded.

## Card

```
Checkpoint: 008 trace viewer
URL:    http://127.0.0.1:8000
Steps:
  1. Send a message in Chat (writes a trace).
  2. Switch to Traces: the trace is listed.
  3. Select it: the timeline shows turn/llm/tool with attributes.
  4. Switch back to Chat: the transcript is intact.
Review:
  - [x] the list shows recent traces (id, duration, span count, status)
  - [x] the timeline renders turn with llm/tool children and attributes
  - [x] switching views preserves the chat
Clauses: OB-4, WV-1, WV-6, WV-7, WV-8
Features: 008
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/008-trace-viewer/checkpoint.png`

| Check | Result |
| --- | --- |
| Traces list shows recent traces (`4` traces, "N spans") | pass |
| Timeline renders `turn`, `llm`, `tool` spans | pass |
| Span attributes shown (`prompt_tokens`, `cost_cny`, tool name/output) | pass |
| Children indented under `turn` | pass |
| Switching back to Chat preserves the transcript | pass |
| Console errors | 0 |

## Notes

- The viewer is read-only and consumes the 007 API; no backend change.
- No router: the Chat/Traces toggle is client-side state.
- `buildSpanTree` treats an unknown parent as a root, so no span is dropped.
