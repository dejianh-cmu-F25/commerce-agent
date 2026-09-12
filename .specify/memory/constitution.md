# Commerce Agent Constitution

An interview-grade, spec-driven commerce agent. Two faces: a **shopping agent**
for consumers and a **merchant agent** for operators. Single agent, skills, tools,
and a harness that makes model decisions trustworthy.

---

## Core Principles

### P1. Specification Is the Source of Truth
Behavior is defined by specs and contracts, not by implementation. Any behavior
change updates the spec first, then converges the code.
**Rationale:** a non-deterministic system needs a traceable definition of behavior.

### P2. One Agent, Skills, Tools
A single agent owns the whole conversation. Modularity comes from skills and tools.
No multi-agent orchestration in the core.
**Rationale:** commerce conversations are tightly coupled across intents; handoffs lose state.

### P3. Model Proposes, Harness Disposes
The model only proposes. Checkout renders the cart and never charges. Every merchant
write is staged and applied only after host approval.
**Rationale:** money and business changes are irreversible and must be controlled by deterministic code.

### P4. Grounding Is Non-Negotiable
Prices, stock, and policy facts come only from tool results in this session. Writes
and renders accept only server-issued IDs.
**Rationale:** hallucination and prompt injection are the trust boundary in commerce.

### P5. Contract First, Dependency Inversion
Tool schemas, backend interfaces, and replaceable components are defined as contracts
before implementations. Implementations are injected.
**Rationale:** changeable parts must be replaceable and testable in isolation.

### P6. Simplicity Over Cleverness
Prefer the simplest design that works. Add complexity only when it demonstrably pays off.
**Rationale:** readability and maintainability outrank cleverness.

### P7. Evals Are First-Class
Every feature ships with positive and negative acceptance cases. Passing evals is part
of the definition of done.
**Rationale:** quality of a non-deterministic system can only be guaranteed by evaluation.

### P8. Reproducible by Default
Mock data, single-command startup, and no paid dependency required to demonstrate the
core path.
**Rationale:** interviews, collaboration, and regression all require reproducibility.

---

## PB — Ports & Boundaries

- **PB-1 Config as Contract.** Every replaceable component is selected by
  `config/settings.yaml` and validated. No hardcoded providers, models, or paths.
  Misconfiguration fails loud at load; never silently falls back.
- **PB-2 Capability Seam.** A replaceable capability is three roles:
  **Service Definition + Service Provider + Consumer**. One role alone is not a seam.
  Build a seam only for a capability with a config switch or a second plausible implementation.
- **PB-3 Explicit at Boundaries.** Defaulting is an explicit `resolve(request) -> Spec`
  step; never a hidden fallback inside `run()`. Split only where defaulting is non-trivial.
- **PB-4 Prompts Are External.** All prompts live under `config/prompts/`. No inline prompt
  strings in code. LLM-backed steps expose a `use_llm`-style switch.
- **PB-5 Validate at Real Boundaries Only.** Validate at config, model JSON, tool JSON,
  durable storage, and wire boundaries. Do not re-validate typed same-process values.

## SL — Session Log & Observability

- **SL-1 Model-Visible Means Logged (NON-NEGOTIABLE).** Model messages are built **only**
  from the session log. Every request verifies that the assembled context equals the
  log-derived context; a mismatch crashes the process.
- **SL-2 Structured Traces.** Every pipeline (agent turn, tool call, retrieval, memory,
  ingestion) emits a structured trace to `logs/traces.jsonl` with a `trace_id`, plus
  structured logs.

## WV — Web-Visible Acceptance

- **WV-1** Each feature spec **should** include `## Web Acceptance` and `## Observability`.
- **WV-2** A feature **should** be demonstrable in the browser; the demonstration is
  recorded in the PR description.
- **WV-3** UI is registered in a **component registry** (`component_type -> renderer`).
  The generic renderer renders any registered type. A new component type is part of that
  feature's deliverable.
- **WV-4** The web app provides a **Scenario Runner** and an **Observability** page.
- **WV-5** Backend-only features still expose a web-triggerable entry (admin page or runner).
- Enforcement is a convention plus a `feature-close` reminder, not a hard gate.

## OB — Observability

- **OB-1** `trace_id` spans agent turn, tool call, retrieval, memory, and ingestion.
- **OB-2** Structured logs only; no bare prints.
- **OB-3** Metrics: latency, tokens, cost, cache hit, tool success/failure.
- **OB-4** A web Trace Viewer: browse sessions, view the turn/step/tool timeline, replay.
- **OB-5** Each span records redacted inputs and outputs.

## DP — Deployment

- **DP-1** `docker compose up` starts the app and its dependencies.
- **DP-2** All configuration comes from environment variables; no secrets in the image;
  ship `.env.example`.
- **DP-3** `/healthz` (liveness) and `/readyz` (readiness).
- **DP-4** Multi-stage build, non-root user, reproducible.
- **DP-5** CI builds the image and runs a container smoke test.
- **DP-6** Persistent volumes for SQLite, Chroma, and traces.

## HR — Harness Engineering

- **HR-1** **Agent = Model + Harness.** The harness boundary is explicit: it begins where
  identity, state, policy, budgets, and model invocation are coordinated, and ends at
  explicit adapters to providers, tools, storage, approval, and telemetry.
- **HR-2** The harness owns eight jobs: context assembly, tool mediation, state persistence,
  control, memory, observability, recovery, and delivery.
- **HR-3** **Guides (feedforward) and Sensors (feedback) both exist.** Guides steer before
  acting (prompt, skills, tool contracts). Sensors check after acting (tests, typechecker,
  evals, gates). Neither alone is sufficient.
- **HR-4** Controls are either **computational** (deterministic, fast) or **inferential**
  (semantic, LLM-based). Each has its place.
- **HR-5** Regulate at three levels: maintainability, architecture fitness, and behaviour.
- **HR-6** **Context discipline.** Never dump whole files, logs, or full history into the
  window. Compact context and retain tool results deliberately.
- **HR-7** **Provider-neutral.** The harness does not bind to a model. Model x harness pairs
  are benchmarked on our own gold set.
- **HR-8** Evaluate the harness itself with **deterministic mock tools**.
- **HR-9** Start with the loop, keep scaffolding minimal; do not overengineer.
- **HR-10** Long tasks persist state to disk, record progress, and can resume.
- **HR-11** New behavior attaches to a documented extension point. Changing the loop updates
  the architecture doc. See `docs/architecture.md` ("Where new behavior goes").
- **HR-12 Budgets.** The harness enforces a spend budget. It records token usage per call,
  converts it to the configured currency, and stops the loop with a clear event when the
  budget is exceeded. A console-side hard limit is the deployment's responsibility.

## SR — Self-Review & Checkpoints

- **SR-1** Before opening a pull request, the agent self-reviews the change against every
  clause of this constitution and the feature spec.
- **SR-2** Each clause is marked **AUTO** (automated check passed), **MANUAL** (confirmed with
  a note), or **N/A** (with a reason). No clause is left blank.
- **SR-3** A clause that fails without a recorded waiver **blocks the pull request**.
- **SR-4** When a feature introduces or changes browser-visible content, the agent starts the
  app, opens the page, and presents a review card.
- **SR-5** The review card lists the URL, the steps, the expected result, and the clauses and
  features under review.
- The self-review report lives at `specs/<NNN>-<name>/review.md`.

## DR — Decision Records

- **DR-1** Every non-trivial change adds or updates an Agent Note in the same PR.
- **DR-2** Format: `## Problem` / `## Decision` / `## Alternatives considered` /
  `## Consequences`. `## Alternatives considered` is mandatory.
- **DR-3** Lifecycle `proposed/`, `implemented/`, `rejected/`; classes `architecture`,
  `process`, `testing`. (No bilingual files, no frozen archive.)
- **DR-4** A `verify_notes` gate checks path, `Status`, and the presence of alternatives.
- **DR-5** Boundary: feature-scoped decisions stay in the Spec Kit `plan`/`research`;
  Agent Notes record cross-cutting decisions.

## TT — Testing & Types

- **TT-1** Three tiers: unit (mock externals), integration (real SQLite, fake LLM), e2e.
- **TT-2** Keyless replay: a fixture-driven FakeLLM replays recorded sessions. Assert only
  deterministic outcomes (tool sequence, final state, rendered component), never model prose.
- **TT-3** `pyright` runs in CI.

## RD — Resilience & Data

- **RD-1** Graceful fallback: every LLM-enhanced step has a deterministic fallback and can be
  disabled by config (memory extraction, rerank, chunk refinement, metadata enrichment).
- **RD-2** Idempotent data management: `DocumentManager` guarantees re-ingestion does not
  duplicate data; updates and deletions are traceable.

## GH — GitHub Workflow

- **GH-1** One feature, one branch: `<NNN>-<name>`, created by `/speckit-specify`.
- **GH-2** A feature is done only when merged into `main` via a pull request.
- **GH-3** Human review gate. Solo repository: enforced by the PR checklist (no required approvals).
- **GH-4** Required checks: `lint + typecheck + unit + integration + image build`. Strict,
  squash merge, linear history.
- **GH-5** Traceability: the PR links the spec, lists completed tasks, and reports eval results.
- **GH-6** Delete the branch after merge.

---

## Governance

- `main` is protected: no force push, no deletion, PR required, status checks required,
  conversation resolution required, linear history, bypass disabled. Required approvals are
  not set (solo maintainer).
- Changes to this constitution go through a pull request like any feature.
- All PRs and reviews verify compliance with these principles. Any complexity beyond the
  simplest workable design must be justified in an Agent Note.

**Version**: 1.0.0 | **Ratified**: 2026-09-13 | **Last Amended**: 2026-09-13
