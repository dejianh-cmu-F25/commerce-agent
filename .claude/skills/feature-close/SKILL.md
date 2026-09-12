---
name: feature-close
description: Close out a finished feature by verifying tasks, running the quality gates, and opening a pull request for human review. Use when a feature's tasks are all complete and it is ready to merge, or when the user says "close the feature", "finish feature", "open the PR", or "收尾".
---

# Feature Close

Take a feature from "tasks complete" to "pull request open and awaiting human
review". This skill **never merges** — a human review is required (GH-3).

## Preconditions

- The current branch is the feature branch `<NNN>-<name>` (created by
  `/speckit-specify`).
- `specs/<NNN>-<name>/tasks.md` exists.

## Pipeline

```
Check tasks -> Run gates -> Remind -> Open PR -> Stop
```

### 1. Check tasks

Read `specs/<NNN>-<name>/tasks.md`. Every task must be marked complete. If any
task is open, stop and report which ones.

### 2. Run the quality gates

Run and report the exact commands:

```sh
ruff check . && ruff format --check .
pyright
pytest tests/unit tests/integration -q
python evals/run.py            # only if the feature touches model behavior
python scripts/verify_notes.py
docker build -t commerce-agent:local .
```

If any gate fails, stop and report the failure. Do not open a PR.

### 3. Remind (non-blocking)

Warn — do not fail — if the feature spec is missing either section:

- `## Web Acceptance` (WV-1)
- `## Observability` (WV-1)

Also confirm an Agent Note exists under `docs/notes/` for non-trivial changes
(DR-1). A missing note is a warning, not a blocker, but say so clearly.

### 4. Open the pull request

Create the PR against `main` using `.github/pull_request_template.md`. Fill in:

- the spec path and feature id,
- the completed task list,
- the web acceptance steps,
- the eval result, if any.

### 5. Stop

Print the PR URL and stop. **Do not merge.** Report that the pull request is
awaiting human review, and that after approval it should be squash-merged and
the branch deleted (GH-4, GH-6).
