# Feature Specification: Deployment Hardening

**Feature Branch**: `015-deployment-hardening`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Make deployment honest and verified: align `.env.example` and
`docker-compose.yml` with the configuration the app actually reads, and add a
keyless container smoke test to the local gate so the image is proven to run
(DP-2, DP-3, DP-4, DP-5, DP-6).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The config contract is complete and enforced (Priority: P1)

An operator copies `.env.example` and expects every variable to take effect. The
documented variables, the compose file, and the settings loader agree, and a test
fails if they drift.

**Why this priority**: `.env.example` and compose currently advertise
`SQLITE_PATH`/`CHROMA_PATH`, which the app never reads; following them silently
does nothing. Config that lies is worse than no config (PB-1, DP-2).

**Independent Test**: Parse `.env.example` and `docker-compose.yml`, collect the
env keys they reference, and assert each is a known override and that every known
override is documented.

**Acceptance Scenarios**:

1. **Given** `.env.example`, **When** the parity test runs, **Then** it lists
   exactly the environment variables the settings loader reads.
2. **Given** `docker-compose.yml`, **When** the parity test runs, **Then** every
   env key it sets is a known override.
3. **Given** a new settings override, **When** it is not added to `.env.example`,
   **Then** the parity test fails.

---

### User Story 2 - The image is proven to run, keylessly (Priority: P1)

`make ci-image` builds the image and runs a container smoke test that exercises
the real process with no API key: liveness, readiness, the SPA, and a chat turn.

**Why this priority**: The gate builds the image but never runs it, so a broken
image passes (DP-5). A keyless smoke keeps the check reproducible (P8).

**Independent Test**: Build the image, run it with `LLM_PROVIDER=mock` and the
memory providers, and assert `/healthz`, `/readyz`, `/` (SPA), and `/chat`
respond; assert the process is non-root.

**Acceptance Scenarios**:

1. **Given** the built image, **When** the container starts with a mock model and
   in-memory stores, **Then** `/healthz` returns ok and `/readyz` reports the
   configured providers.
2. **Given** the running container, **When** `/` is fetched, **Then** the SPA
   shell is served; **When** `/chat` is posted, **Then** an SSE turn completes.
3. **Given** the running container, **When** its user is inspected, **Then** it
   is not root (DP-4).
4. **Given** the smoke test ends (pass or fail), **Then** the container is
   removed and the port is released.

---

### User Story 3 - One command brings the stack up with persistent volumes (Priority: P2)

`docker compose up` starts the app with data and logs on the host so state
survives restarts.

**Independent Test**: `docker compose config` validates; the compose file mounts
`./data` and `./logs` and passes config via the environment.

**Acceptance Scenarios**:

1. **Given** `docker-compose.yml`, **When** `docker compose config` runs, **Then**
   it is valid and the app service mounts the data and log volumes (DP-6).
2. **Given** the compose file, **When** the smoke test runs with `--with-image`,
   **Then** it does not depend on `docker compose` (it uses `docker run` so it
   works with or without Compose).

---

### Edge Cases

- **Docker unavailable**: `make ci-fast` never requires Docker; `--with-image`
  fails loud with a clear message when Docker is missing.
- **Port already in use**: the smoke test binds a high, configurable port and
  fails loud if the container cannot start.
- **Slow start**: the smoke test polls `/healthz` with a timeout and a clear
  failure instead of hanging.
- **No `.env`**: the smoke test passes config with `-e` flags and never reads the
  developer's `.env` (no key required).
- **Secret in the image**: `.dockerignore` excludes `.env`; the build context
  never contains secrets (DP-2).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `.env.example` MUST document exactly the environment variables the
  settings loader reads, with comments; no stale keys (PB-1, DP-2).
- **FR-002**: `docker-compose.yml` MUST configure the app using those same
  variable names, and MUST mount persistent volumes for data and logs (DP-6).
- **FR-003**: A test MUST enforce the config contract: every key in
  `.env.example` and in `docker-compose.yml` is a known override, and every known
  override is documented (PB-1).
- **FR-004**: The local gate MUST build the image and run a container smoke test
  when invoked with `--with-image` (DP-5).
- **FR-005**: The smoke test MUST run keylessly (`LLM_PROVIDER=mock`, memory
  storefront/session/memory) and MUST NOT require the developer's `.env` (P8).
- **FR-006**: The smoke test MUST assert `/healthz` ok, `/readyz` reporting the
  configured providers, `/` serving the SPA shell, and `/chat` completing an SSE
  turn.
- **FR-007**: The smoke test MUST assert the container process is not root
  (DP-4) and MUST clean up (remove the container, release the port) on every
  exit path.
- **FR-008**: The image MUST NOT contain secrets; `.dockerignore` MUST exclude
  `.env` and runtime data (DP-2).
- **FR-009**: `docker compose config` MUST validate (DP-1).

### Key Entities

- **Config contract**: the set of environment variable names the settings loader
  accepts, plus their documentation and deployment usage.
- **Smoke test**: a script that runs the built image keylessly and asserts the
  container's HTTP surface and process identity.

## UI Requirements *(when the feature is browser-visible; WV-6..WV-8)*

This feature changes packaging, not the UI. The browser surface is the existing
app, now served from the container; the smoke test asserts the served shell and a
chat turn. No component, state, or style changes.

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | — | Unchanged from features 001–014 |
| Loading / Streaming | — | Unchanged |
| Success | — | Unchanged |
| Error | — | Unchanged |
| Disabled | — | Unchanged |

## Web Acceptance

- The container serves the SPA shell at `/` (title `Commerce Agent`) and a mock
  chat turn completes over SSE — verified by the smoke test, not a new screen.
- `/healthz` and `/readyz` are reachable inside the container (DP-3).

## Observability

- The smoke test prints the readiness payload and the chat turn's terminal event,
  so a failure shows which surface broke.
- Container logs remain the structured logs from the app; the traces volume is
  mounted so `logs/traces.jsonl` persists (OB, DP-6).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The config-parity test passes; a stale or missing key fails it.
- **SC-002**: `make ci-image` builds the image and the smoke test passes
  keylessly.
- **SC-003**: The built image contains no `.env` or key material.
- **SC-004**: `make ci-fast` is unaffected and still passes without Docker.
- **SC-005**: `docker compose config` validates.

## Assumptions

- Docker is available in the development environment; the image build is slow, so
  it stays opt-in (`--with-image`) and is not part of the pre-push fast gate.
- The smoke test uses `docker run`, not `docker compose`, so it works regardless
  of Compose availability; compose is validated separately.
- A keyless mock model is sufficient to prove the container runs; real-provider
  behavior is unchanged and covered by the browser checkpoints.
