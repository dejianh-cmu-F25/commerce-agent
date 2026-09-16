# Commerce Agent

An interview-grade, **spec-driven** full-journey shopping agent built from scratch on a
hand-written agent loop. Two stages of one journey:

- **Discovery** *(planned)*: product search and ranking over a real catalog (ESCI),
  grounded in human relevance labels.
- **Post-purchase** *(implemented)*: order status, returns, and refunds over a real
  store (Shopify), grounded in a versioned retailer policy.

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

## Production constraints

The constitution (v1.3.1) adds three clauses: **RW** (Real-World Fitness),
**SC** (Scale & Operability), and **EV** (Evidence-Backed Change). A feature that
touches inputs, data, the model, or retrieval must fill in `## Real-World
Coverage`; a model / prompt / retrieval / module change must ship before/after
evidence. Details: `docs/production-conventions.md`. The project's current
standing against these clauses: `docs/production-audit.md`.

## Status

Spec-driven demo with 25 features merged. The measured results — retrieval
quality, feature ablation, real-model reliability, process metrics, and cost —
are recorded in [`specs/RESULTS.md`](specs/RESULTS.md), rendered by the app's
**Report** tab, and checked against the keyless artifacts by the local gate.
See `specs/` for the feature list.

## Quick start

```sh
cp .env.example .env        # add your DeepSeek API key
uv sync                     # install dependencies
docker compose up --build   # app (SQLite embedded; data/logs on host volumes)
```

Then open the web UI and chat with the agent.

## Deployment

- Config is one contract: `.env.example` lists exactly the variables the app
  reads, and a test enforces parity with `docker-compose.yml` (PB-1, DP-2).
- `make ci-image` builds the image and runs a **keyless container smoke test**
  (`scripts/smoke_container.sh`): liveness, readiness, the SPA, a chat turn, and a
  non-root process — no API key required (DP-3..DP-5).
- `make ci-fast` (the pre-push gate) stays fast and Docker-free.
- On slow networks, accelerate the build with mirrors (all opt-in; defaults stay
  official):
  ```sh
  NPM_REGISTRY=https://registry.npmmirror.com \
  UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple \
  make ci-image
  ```
  Base images use the Docker daemon's `registry-mirrors` (e.g. add
  `"registry-mirrors": ["https://docker.m.daocloud.io"]` in Docker Desktop →
  Settings → Docker Engine).

## Layout

The repository layout, layers, and data flow live in
[`docs/architecture.md`](docs/architecture.md) (single source of truth). The
feature specs are in `specs/<NNN>-<name>/`; decisions are in `docs/notes/`.

## License

MIT
