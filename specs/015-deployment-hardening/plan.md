# Implementation Plan: Deployment Hardening

**Branch**: `015-deployment-hardening` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/015-deployment-hardening/spec.md`

## Summary

Fix the config contract: `.env.example` and `docker-compose.yml` are rewritten to
use the exact environment variable names the settings loader reads, enforced by a
unit test. Add `scripts/smoke_container.sh`, a keyless container smoke test, and
run it from `scripts/ci.sh --with-image` after the image build. No application
code changes.

## Technical Context

**Language/Version**: Bash; Python 3.13 for the config test; Docker

**Primary Dependencies**: Docker (build + run); no new Python or JS dependency

**Storage**: host volumes `./data` (SQLite) and `./logs` (traces)

**Testing**: `pytest` unit test that parses `.env.example` and
`docker-compose.yml` and checks parity with `_ENV_OVERRIDES`; a shell smoke test

**Target Platform**: container runtime (Linux, non-root)

**Performance Goals**: the smoke test is off the fast path (only `--with-image`)

**Constraints**: keyless smoke (mock model, memory providers); no secrets in the
image; cleanup on every exit path

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| PB-1 config as contract | `.env.example`/compose match `_ENV_OVERRIDES`; a test enforces parity | PASS |
| P8 reproducible | smoke runs keylessly with no key and no network model | PASS |
| DP-1 single command | `docker compose config` validated | PASS |
| DP-2 env-only, no secrets | `.dockerignore` excludes `.env`; compose passes config via env | PASS |
| DP-3 health endpoints | smoke asserts `/healthz` and `/readyz` | PASS |
| DP-4 non-root, multi-stage | smoke asserts the container uid is not 0 | PASS |
| DP-5 gate builds + smoke | `scripts/ci.sh --with-image` runs the smoke test | PASS |
| DP-6 persistent volumes | compose mounts `./data` and `./logs` | PASS |
| GH-4 local gate | fast gate unchanged; image smoke is opt-in | PASS |

## Project Structure

```text
.env.example                 # rewritten to the real config contract
docker-compose.yml           # real env names + volumes
scripts/smoke_container.sh   # NEW: keyless container smoke test
scripts/ci.sh                # run the smoke test under --with-image
Makefile                     # + smoke-image convenience target
tests/unit/test_deploy_config.py  # NEW: config parity test
docs/notes/implemented/architecture/...-deployment-hardening.md
```

## Design decisions

- **Parity is a test, not a comment.** The contract lives in `_ENV_OVERRIDES`;
  `.env.example` and compose are checked against it, so drift fails the gate.
- **The smoke test uses `docker run`, not `docker compose`.** Compose is
  validated separately with `docker compose config`; the smoke test then works
  even where Compose is unavailable and controls the port and cleanup directly.
- **Keyless by construction.** The smoke test sets `LLM_PROVIDER=mock` and the
  memory providers and never reads `.env`, so it needs no key and spends nothing
  (P8, HR-12).
- **Off the fast path.** The image build and smoke stay behind `--with-image`
  (and `make ci-image`); the pre-push gate is unchanged.

## Complexity Tracking

> No constitution violations. The feature adds a shell script and a test; it
> changes no application code.
