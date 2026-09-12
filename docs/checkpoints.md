# Checkpoints

A checkpoint is a moment where the agent starts the app, opens the page, and
hands the reviewer a card describing what to look at (constitution SR-4, SR-5).

## Trigger

A feature triggers a checkpoint when its `spec.md` has a non-empty
`## Web Acceptance` section — that is, when it introduces or changes
browser-visible content.

Backend-only features still expose a web entry where practical (WV-5). A feature
with no browser surface at all records why in its review.

## Running a checkpoint

```sh
./scripts/serve.sh          # real DeepSeek, opens the browser
NO_OPEN=1 ./scripts/serve.sh   # headless
```

Endpoints: `/` chat, `/budget`, `/healthz`, `/readyz`.

## Review card template

```
Checkpoint: <feature id and name>
URL:    http://localhost:8000
Steps:
  1. <action>
  2. <expected result>
Review:
  - [ ] <clause or behavior to verify>
  - [ ] <clause or behavior to verify>
Clauses: <constitution clauses under review>
Features: <feature ids>
```

## Checkpoint log

| Checkpoint | Features | What to review | Status |
| --- | --- | --- | --- |
| 001 agent core | 001 | chat, SSE streaming, tool call, budget, health | pending review |
