# Commerce Agent

An interview-grade, **spec-driven** commerce agent built from scratch on a hand-written
agent loop. Two faces:

- **Shopping agent** for consumers: discover, compare, plan, cart, checkout handoff,
  post-purchase care, and cross-session memory.
- **Merchant agent** for operators: analytics, inventory, pricing, promotions, and
  campaigns — every write staged and applied only after approval.

The model (DeepSeek, provider-neutral) proposes. The harness disposes.

## Why this project exists

It is a study in **harness engineering**: the software around a model that makes its
decisions trustworthy. See `.specify/memory/constitution.md` for the governing principles
and `docs/architecture.md` for the runtime shape and data flow.

## Method

This repository is developed **spec-first** with [GitHub Spec Kit](https://github.com/github/spec-kit):

```
/speckit-constitution -> /speckit-specify -> /speckit-plan -> /speckit-tasks
  -> /speckit-implement -> /speckit-converge
```

Each feature lives in `specs/<NNN>-<name>/` on its own branch and merges through a pull
request that satisfies the review checklist.

## Status

Early scaffold. See `specs/` for the feature backlog.

## Quick start

```sh
cp .env.example .env        # add your DeepSeek API key
uv sync                     # install dependencies
docker compose up --build   # app (SQLite embedded; data/logs on host volumes)
```

Then open the web UI and try the Scenario Runner.

## Deployment

- Config is one contract: `.env.example` lists exactly the variables the app
  reads, and a test enforces parity with `docker-compose.yml` (PB-1, DP-2).
- `make ci-image` builds the image and runs a **keyless container smoke test**
  (`scripts/smoke_container.sh`): liveness, readiness, the SPA, a chat turn, and a
  non-root process — no API key required (DP-3..DP-5).
- `make ci-fast` (the pre-push gate) stays fast and Docker-free.

## Layout

```
.specify/        Spec Kit config, templates, and the constitution
specs/           One directory per feature (spec, plan, tasks, contracts)
app/             core (loop, session), ports, adapters, tools, skills, memory, gates, trace
config/          settings.yaml and prompts
web/             FastAPI + SSE chat, scenario runner, observability, admin
evals/           Evaluation cases, fixtures, and the replay runner
tests/           unit / integration / e2e
docs/            architecture, decisions (Agent Notes), demo
scripts/         sync_spec, verify_notes
```

## License

MIT
