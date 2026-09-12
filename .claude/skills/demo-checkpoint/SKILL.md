---
name: demo-checkpoint
description: Start the app, open the browser, and present a review card describing what a human should look at. Use when a feature introduces browser-visible content, or when the user says "show me", "open the page", "demo", "起服务", "开页面", or "演示".
---

# Demo Checkpoint

Turn a finished chunk of work into a browser review session (SR-4, SR-5).

## Preconditions

- The feature's tasks are complete and `spec-review` has passed.
- `specs/<NNN>-<name>/spec.md` has a non-empty `## Web Acceptance` section
  (otherwise this checkpoint does not apply).

## Pipeline

```
Start server -> Wait for health -> Open browser -> Print the review card
```

### 1. Start the server

```sh
./scripts/serve.sh
```

Uses the real provider from `.env` and opens the browser. Use
`NO_OPEN=1 ./scripts/serve.sh` for a headless start. For the deployment
checkpoint, use `docker compose up --build` instead.

### 2. Wait for health

Poll `/healthz` until it returns ok. Report the URL and the current `/budget`.

### 3. Print the review card

Fill in `docs/checkpoints.md`'s template for this feature:

- **URL**
- **Steps**: the exact actions to take, from the spec's Web Acceptance section.
- **Review**: checkboxes tied to specific behaviors and clauses.
- **Clauses / Features**: what is under review.

### 4. Hand over

Tell the user what to click and what to expect. **Do not proceed to merge.** Wait
for the user's review, then record the outcome in `docs/checkpoints.md`.
