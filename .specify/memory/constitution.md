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
Every feature ships with positive and negative acceptance cases. Change evidence and the
definition of done for a change are governed by EV.
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
- **WV-6 UI States.** A browser-visible feature spec **must** enumerate its UI states —
  empty, loading/streaming, success, error, and disabled — and define the behavior of each.
  A happy-path-only spec is incomplete.
- **WV-7 Accessibility.** Interactive UI **must** be keyboard-operable with a visible focus
  ring; streamed content is announced with `aria-live`; motion respects
  `prefers-reduced-motion`; text inputs are at least 16px.
- **WV-8 Responsive & Theme.** The UI **must** be usable from 375px to desktop and **must**
  follow the system color scheme (`prefers-color-scheme`).
- **WV-9 Rendering Safety.** Any model- or user-derived markup rendered into the DOM **must**
  be sanitized first; raw HTML injection is forbidden.
- Enforcement is a convention plus a `feature-close` reminder, not a hard gate. The
  checklist and details live in `docs/ui-conventions.md`.

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
- **DP-4** Multi-stage build, non-root user, reproducible (see P8).
- **DP-5** The local gate builds the image (`scripts/ci.sh --with-image`) and runs a
  container smoke test.
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
  `process`, `testing`, `production`. (No bilingual files, no frozen archive.)
- **DR-4** A `verify_notes` gate checks path, `Status`, and the presence of alternatives.
- **DR-5** Boundary: feature-scoped decisions stay in the Spec Kit `plan`/`research`;
  Agent Notes record cross-cutting decisions.

## TT — Testing & Types

- **TT-1** Three tiers: unit (mock externals), integration (real SQLite, fake LLM), e2e.
- **TT-2** Keyless replay: a fixture-driven FakeLLM replays recorded sessions. Assert only
  deterministic outcomes (tool sequence, final state, rendered component), never model prose.
- **TT-3** `pyright` runs in the local gate (`scripts/ci.sh`).

## RD — Resilience & Data

- **RD-1** Graceful fallback: every external dependency and LLM-enhanced step has a
  deterministic fallback and can be disabled by config (memory extraction, rerank, chunk
  refinement, metadata enrichment); the system degrades observably rather than failing
  silently. This is the single owner of the fallback rule (see RW).
- **RD-2** Idempotent data management: `DocumentManager` guarantees re-ingestion does not
  duplicate data; updates and deletions are traceable.

## RW — Real-World Fitness

This project must be genuinely useful, not a demo that looks good until real
traffic arrives. Features that interpret free-form input or handle data MUST
address the real world, not the happy path. Enforcement is the spec's
`## Real-World Coverage` section plus the checklist in
`docs/production-conventions.md`. Fallback is owned by RD-1.

- **RW-1 Input distribution.** A feature that interprets free-form input MUST
  enumerate the real input space — phrasings, ambiguity, languages, and
  adversarial inputs — and define behavior for **unseen / out-of-distribution**
  input, including when to ask for clarification and when to refuse. A single
  happy-path phrasing is not a specification.
- **RW-2 Data quality.** Every data boundary MUST validate and normalize; missing,
  dirty, or conflicting data MUST have **defined behavior and a repair path**.
  No silent assumptions about upstream data.
- **RW-3 Edge & failure modes.** A spec MUST enumerate its edge and failure modes
  and define behavior for each. An undefined boundary is a defect, not a
  production discovery.
- **RW-4 No patchwork.** A fix MUST address the **root cause** and ship with a
  **regression case** (end-to-end and, where useful, trajectory-prefix). A
  one-off special case without a regression is incomplete.

**Rationale:** the failure mode this project must avoid is a narrow demo that
collapses under real phrasing, dirty data, and unexpected boundaries, and that is
"fixed" by patching.

## SC — Scale & Operability

A system that works small and falls apart at scale, that a team cannot diagnose,
or that cannot be changed safely, is not done.

- **SC-1 Scale envelope.** A spec MUST state the scale dimensions it must survive
  — traffic, data volume, concurrency, tenancy, session length — and the
  **measured** behavior at that boundary. "It works small" is not a claim.
- **SC-2 Diagnosability.** Every failure MUST be attributable (trace + first
  error; the span/trace rules are owned by OB), and metrics MUST be
  **segmentable** (by intent, tool, model, tenant) so a team can localize a
  problem under load.
- **SC-3 SLOs.** Latency, cost, and error budgets MUST be declared and tracked;
  regressions MUST be visible.
- **SC-4 Change safety.** Changes MUST be localized behind seams; the **blast
  radius** and the migration / rollback path MUST be stated. No big-bang
  rewrites.

**Rationale:** scale exposes problems in clusters, and a team that cannot locate
them or change the system safely will stall.

## EV — Evidence-Backed Change

No change to the model, a prompt, retrieval, or a module is accepted on
reputation. It ships with proof. Enforcement is the PR checklist plus
`scripts/check_change_evidence.py`.

- **EV-1 No unmeasured change.** Every change MUST have a dated, auditable entry in
  the change log (`specs/change-log.json`, rendered into the `## Change log` of
  `specs/RESULTS.md` and `evals/report.md`) recording **what changed**. A change to
  the model, a prompt, retrieval, a tool, the agent logic, or data MUST also record
  a **quantified `before → after`** on a fixed, representative benchmark, with
  guardrails. A change with no measurable behavior MUST declare that and why.
- **EV-2 Paired and significant.** Comparisons MUST be **paired** on the same
  tasks with multiple seeds; effect size, confidence, and sample size MUST be
  reported. A single run selects direction, it does not prove improvement.
- **EV-3 Guardrails.** Quality, safety (zero ungrounded writes), latency, and cost
  are **guardrail** metrics. A change that improves the target but regresses a
  guardrail MUST be rejected.
- **EV-4 Versioning.** Model and prompt versions — including a hash of the
  rendered system prompt — MUST be recorded with the results.
- **EV-5 Regression sets.** Production failures MUST become end-to-end and
  trajectory-prefix regression cases.
- **EV-6 Auditability.** Every merged change MUST be reconstructable from the change
  log alone: the change id, date, what changed, the metric, the before/after, the
  guardrails, the verdict, and a link to the evidence. A change that cannot be
  audited this way is not done.

**Definition of done (evidence).** A model, prompt, retrieval, or module change is
done only when `specs/change-log.json` holds a dated entry with a metric and a
quantified `before → after`; a change with no measurable behavior is done when its
entry declares that and why.

**Rationale:** a team that cannot prove a change improved the project cannot
justify the change, and will drift into unmeasured churn.

## GH — GitHub Workflow

- **GH-1** One feature, one branch: `<NNN>-<name>`, created by `/speckit-specify`.
- **GH-2** A feature is done only when merged into `main` via a pull request.
- **GH-3** Human review gate. Solo repository: enforced by the PR checklist (no required approvals).
- **GH-4** The gate is **local**: run `scripts/ci.sh` (ruff + format, pyright, pytest
  unit+integration, spec self-review, agent-notes; frontend lint, typecheck, test, build)
  before pushing. Docker image build is optional (`scripts/ci.sh --with-image`). Squash
  merge, linear history.
- **GH-5** Traceability: the PR links the spec, lists completed tasks, and reports eval results.
- **GH-6** Delete the branch after merge.

---

## Governance

- `main` is protected: no force push, no deletion, PR required, conversation
  resolution required, linear history, bypass disabled. Required approvals are
  not set (solo maintainer). The gate is the local `scripts/ci.sh` plus the PR
  checklist; there are no GitHub status checks.
- Changes to this constitution go through a pull request like any feature.
- All PRs and reviews verify compliance with these principles. Any complexity beyond the
  simplest workable design must be justified in an Agent Note.
- The production clauses (RW / SC / EV) are applied **proportionally** (P6): the hard gate
  checks are narrow (a spec section exists, a change-log entry exists, a measurable entry
  carries numbers); semantic judgments — root cause, blast radius, data contracts — are
  reviewer-owned and recorded, not automated.

**Version**: 1.3.1 | **Ratified**: 2026-09-13 | **Last Amended**: 2026-09-13
