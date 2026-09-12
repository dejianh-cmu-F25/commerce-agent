# Browser checkpoint: 015-deployment-hardening

Constitution SR-4 / SR-5. This feature changes packaging, not the UI, so there is
**no new browser surface** to review. The intended acceptance is the keyless
container smoke test (DP-5); it is implemented and wired into
`scripts/ci.sh --with-image`, but **was not executed in this environment**.

## Card

```
Checkpoint: 015 deployment hardening
URL:    (container) http://127.0.0.1:18080
Steps:
  1. scripts/smoke_container.sh commerce-agent:ci
  2. Assert /healthz, /readyz, the SPA shell, a /chat turn, and a non-root uid.
Review:
  - [ ] container smoke passes end-to-end  (DEFERRED — see below)
Clauses: PB-1, P8, DP-1..DP-6
Features: 015
```

## Result

- Date: 2026-09-13
- Status: **DEFERRED** (container smoke not run in this environment)
- Evidence: this file; the config tests; local HTTP assertions (below)

| Check | Result |
| --- | --- |
| `.env.example` documents exactly the settings overrides | pass (`tests/unit/test_deploy_config.py`) |
| `docker-compose.yml` uses only known env keys | pass |
| `.dockerignore` excludes `.env`, `data`, `logs` | pass |
| `docker compose config` validates | pass |
| `scripts/smoke_container.sh` syntax (`bash -n`) | pass |
| Smoke assertions against the app locally (mock/memory) | pass |
| Container image build + smoke | **deferred** |

### Why the container smoke is deferred

Docker Hub throughput in this environment is ~90 KB/s (`docker pull
alpine:3.19`, 3 MB, took 33 s; GitHub ~63 KB/s). A full multi-stage build pulls
`node:20-alpine` + `python:3.12-slim` + `npm ci` (~480 MB of frontend deps) +
`uv sync` — ~500 MB+, i.e. **45–60+ minutes**. The build is correct; it is simply
impractical to run here. Decision (with the maintainer): merge with the smoke
recorded as deferred and run `make ci-image` on a faster network.

### Local equivalent (no Docker)

With `LLM_PROVIDER=mock` and the memory providers, the app served:
`/healthz` → ok; `/readyz` → `{"storefront":"memory","memory":"memory"}`; `/` →
the SPA shell (`<title>Commerce Agent</title>`); `POST /chat` → an SSE stream
ending in `"type": "TurnEnd"`. These are exactly the assertions the container
smoke makes.

## Notes

- No application code changed; the fast gate (`make ci-fast`) is unaffected and
  remains Docker-free.
- The smoke test uses `docker run` (not Compose) and cleans up on every exit
  path; Compose is validated separately.
