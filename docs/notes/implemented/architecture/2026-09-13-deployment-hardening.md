# Agent Note: Deployment config is one contract, proven by a keyless container smoke

Status: implemented (2026-09-13) — feature `015-deployment-hardening`

## Problem

The deployment surface had drifted from the app:

1. `.env.example` and `docker-compose.yml` advertised `SQLITE_PATH` and
   `CHROMA_PATH`, which the settings loader never reads. An operator following
   them would change nothing — config that lies (PB-1, DP-2).
2. The gate built the image but never ran it, so a broken image passed (DP-5).
3. There was no automated proof that the container serves health, the SPA, and a
   chat turn, or that it runs non-root.

## Alternatives considered

- **Keep the docs and fix them by hand.** Cheap, but the same drift recurs. A
  test that derives the contract from the loader is durable.
- **Validate config with a schema tool (e.g. a compose lint).** Catches syntax,
  not the semantic mismatch between compose and the app. Rejected as insufficient.
- **Run the smoke test inside `ci-fast`.** Stronger, but it forces a slow image
  build on every push. Rejected: keep the fast gate fast; the smoke stays behind
  `--with-image`.
- **Smoke via `docker compose up`.** Closer to the documented path, but couples
  the test to Compose and makes port/cleanup control awkward. Rejected in favor of
  `docker run` plus a separate `docker compose config` validation.
- **Use the real provider in the smoke.** More realistic, but needs a key, spends
  budget, and is nondeterministic. Rejected: a keyless mock proves packaging (P8).

## Decision

- **The config contract is `_ENV_OVERRIDES`.** `.env.example` documents exactly
  those keys and `docker-compose.yml` sets a subset of them; a unit test parses
  both and fails on drift. `.dockerignore` is checked to exclude `.env` and
  runtime data.
- **The container smoke test is keyless and self-cleaning.** It runs the image
  with `LLM_PROVIDER=mock` and memory providers, asserts `/healthz`, `/readyz`,
  the SPA shell, a completed `/chat` turn, and a non-root uid, then removes the
  container on every exit path.
- **The smoke test runs only under `--with-image`** (and `make ci-image`), after
  the image build; the pre-push fast gate is unchanged.
- **Build mirrors are opt-in build args, not hardcoded defaults.** The image
  build takes `NPM_REGISTRY` (npm) and `UV_DEFAULT_INDEX` (Python); `scripts/ci.sh`
  forwards them from the environment. Base images use the Docker daemon's
  `registry-mirrors`. Defaults stay the official registries, so the image remains
  reproducible anywhere; slow networks opt in explicitly
  (`chore/docker-build-mirrors`).

## Consequences

- Adding a settings override without documenting it in `.env.example` now fails
  the gate, so the contract cannot silently drift.
- The image build and smoke remain opt-in (the pre-push fast gate is Docker-free),
  but with mirrors the build is practical: the smoke was executed and passed
  (`healthz ok`, `readyz {"storefront":"memory","memory":"memory"}`, `spa ok`,
  `chat ok`, `uid 10001`).
- The smoke uses a mock model, so it proves the packaging, not provider behavior;
  provider paths stay covered by the browser checkpoints.
- Mirror configuration is environment-specific and not committed; the repository
  only carries the switches.
