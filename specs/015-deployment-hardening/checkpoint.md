# Browser checkpoint: 015-deployment-hardening

Constitution SR-4 / SR-5. This feature changes packaging, not the UI, so there is
**no new browser surface** to review. The acceptance is the keyless container
smoke test (DP-5); it is implemented, wired into `scripts/ci.sh --with-image`, and
now **executed and passing** (after accelerating the build with regional mirrors;
see feature `chore/docker-build-mirrors`).

## Card

```
Checkpoint: 015 deployment hardening
URL:    (container) http://127.0.0.1:18080
Steps:
  1. scripts/smoke_container.sh commerce-agent:ci
  2. Assert /healthz, /readyz, the SPA shell, a /chat turn, and a non-root uid.
Review:
  - [x] container smoke passes end-to-end
Clauses: PB-1, P8, DP-1..DP-6
Features: 015
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: this file; the smoke output below; the config tests

| Check | Result |
| --- | --- |
| `.env.example` documents exactly the settings overrides | pass (`tests/unit/test_deploy_config.py`) |
| `docker-compose.yml` uses only known env keys | pass |
| `.dockerignore` excludes `.env`, `data`, `logs` | pass |
| `docker compose config` validates | pass |
| `scripts/smoke_container.sh` syntax (`bash -n`) | pass |
| Container image build | pass |
| Container smoke: `/healthz`, `/readyz`, SPA, `/chat`, non-root | **pass** |

### Smoke output

```
== container smoke: image commerce-agent:ci ==
healthz: ok
readyz:  {"status":"ready","storefront":"memory","memory":"memory"}
spa:     ok
chat:    ok
user:    uid 10001 (non-root)
OK: container smoke passed
```

### How it was made feasible

Docker Hub throughput here is ~90 KB/s (`alpine:3.19`, 3 MB, 33 s), so the
~500 MB multi-stage build was impractical. It was accelerated with regional
mirrors (see the `chore/docker-build-mirrors` change):

- Docker base images via the Docker Desktop registry mirror
  `https://docker.m.daocloud.io` (`docker info` reports it).
- `npm ci` via `--build-arg NPM_REGISTRY=https://registry.npmmirror.com`.
- `uv sync` via `--build-arg UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`.

## Notes

- No application code changed; the fast gate (`make ci-fast`) is unaffected and
  remains Docker-free.
- The smoke test uses `docker run` (not Compose), runs keylessly (`LLM_PROVIDER=mock`
  + memory providers), and cleans up on every exit path; Compose is validated
  separately with `docker compose config`.
