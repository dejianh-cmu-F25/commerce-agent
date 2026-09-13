# Measured Results

The canonical index of what this project measured. The full tables are rendered
into [`evals/report.md`](../evals/report.md) by the gate; the per-change,
auditable record is the **change log** below. Each feature spec carries a
`## Measured Results` section with its slice.

**Provenance**

| Field | Value |
| --- | --- |
| Date | 2026-09-13 |
| Agent model | `deepseek-flash` |
| Rendered prompt hash | `8578920a4f16` |
| Judge model | `deepseek-chat` |
| Seeds | 3 |
| Embedding | keyless `hash` (256 dims) |
| Vector stores | `memory`, `chroma` |
| Full tables | `evals/report.md` |
| Change log (source) | `specs/change-log.json` |

**Reproduce**

- Keyless (in the gate): `make ci-fast` runs `evals/bench.py` and
  `evals/ablation.py`, then renders `evals/report.md` via
  `uv run python evals/report.py --write` (which also refreshes the change log
  below).
- Real model (opt-in, snapshot): `uv run python evals/agent_eval.py --real
  --seeds 3`. These numbers are a **dated snapshot** and are **not** regenerated
  by the gate.
- Budget: **¥0.5764 / ¥10.00** spent across all runs (harness-enforced, HR-12).

## Headline (2026-09-13 snapshot)

- **Retrieval**: dense retrieval closes the hard-query gap (hit-rate@3
  0.800 → 1.000); TF-IDF overall 0.963.
- **Ablation** (keyless gold set): memory **+0.167**, skills **+0.083**.
- **Real** (DeepSeek, 6 templates × 3 seeds): Pass@1 **0.778** · Pass@k 1.000 ·
  Pass^k **0.667**; 0 ungrounded attempts; 0 judge vetoes; **¥0.0949**.
- **Deployment**: keyless container smoke PASS (non-root, health, SPA, chat).
- **Gate**: 131 tests, gold scenarios 12/12, 18 Agent Notes.

## Change log

Every merged change, auditable: date, what changed, and the quantified
`before → after` where measurable. Generated from `specs/change-log.json`.

<!-- change-log:start -->
| Date | Change | Area | Class | What changed | Metric | Before → After | Guardrails | Verdict | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-13 | init | repo | `docs` | Initialize the spec-driven commerce agent | — | — | — | accepted | `7944888` |
| 2026-09-13 | #1 001-agent-core | agent | `unmeasured` | Agent loop, session log, and SSE web surface | — | No benchmark existed at the time | — | accepted | `specs/001-agent-core` |
| 2026-09-13 | #2 web-ui-conventions | docs | `docs` | Add web UI specification conventions | — | — | — | accepted | `docs/ui-conventions.md` |
| 2026-09-13 | #3 002-web-experience | web | `unmeasured` | Markdown, tool steps, sources, stop/retry, a11y, theme | — | No benchmark existed at the time | — | accepted | `specs/002-web-experience` |
| 2026-09-13 | #4 003-react-web-ui | web | `unmeasured` | React 19 + AI Elements SPA with a custom transport | — | No benchmark existed at the time | — | accepted | `specs/003-react-web-ui` |
| 2026-09-13 | #5 fix responsive-layout | web | `no-behavior` | Responsive layout fix | — | UI-only; no metric | — | accepted | `6246672` |
| 2026-09-13 | #6 fix fluid-column | web | `no-behavior` | Fluid content column | — | UI-only; no metric | — | accepted | `ad7c831` |
| 2026-09-13 | #7 perf web-bundle | web | `measurable` | Cut the initial bundle size | web bundle gzip (kB, index chunk) | 533 → 299 | — | accepted | `958c4b4` |
| 2026-09-13 | #8 chore local-ci | process | `docs` | Replace GitHub Actions with a local CI gate | — | — | — | accepted | `scripts/ci.sh` |
| 2026-09-13 | #9 004-storefront-backend | storefront | `unmeasured` | Storefront backend port (memory + sqlite) | — | No benchmark existed at the time | — | accepted | `specs/004-storefront-backend` |
| 2026-09-13 | #10 005-session-persistence | session | `unmeasured` | Persist sessions (memory + sqlite), resume by id | — | No benchmark existed at the time | — | accepted | `specs/005-session-persistence` |
| 2026-09-13 | #11 006-browser-resume | web | `unmeasured` | Rehydrate the transcript on reload | — | No benchmark existed at the time | — | accepted | `specs/006-browser-resume` |
| 2026-09-13 | #12 007-observability | observability | `unmeasured` | Tracer port + JSONL spans | — | No benchmark existed at the time | — | accepted | `specs/007-observability` |
| 2026-09-13 | #13 008-trace-viewer | web | `unmeasured` | Chat/Traces toggle and span timeline | — | No benchmark existed at the time | — | accepted | `specs/008-trace-viewer` |
| 2026-09-13 | #14 009-cart-checkout | cart | `unmeasured` | Grounded add-to-cart and render-only checkout | — | No benchmark existed at the time | — | accepted | `specs/009-cart-checkout` |
| 2026-09-13 | #15 010-merchant-agent | merchant | `unmeasured` | Staged changes with human-only approval | — | No benchmark existed at the time | — | accepted | `specs/010-merchant-agent` |
| 2026-09-13 | #16 011-evaluation | evaluation | `measurable` | Keyless gold-scenario harness | gold scenarios passing | The gold set has since grown to 12 | — | accepted | `evals/run.py` |
| 2026-09-13 | #17 012-knowledge-retrieval | retrieval | `measurable` | Keyless TF-IDF retrieval over policy docs | retrieval hit-rate@3 (tfidf) | Measured later by the 022 benchmark | — | accepted | `evals/bench.py` |
| 2026-09-13 | #18 013-customer-memory | memory | `measurable` | Cross-session customer memory | gold pass rate (ablation) | 0.75 → 0.917 | 0 ungrounded | accepted | `evals/ablation.py` |
| 2026-09-13 | #19 014-post-purchase | orders | `unmeasured` | Order status and policy-gated returns | — | No benchmark existed at the time | — | accepted | `specs/014-post-purchase` |
| 2026-09-13 | #20 015-deployment-hardening | deployment | `measurable` | Config contract + keyless container smoke | container smoke (pass=1) | 0 → 1 | — | accepted | `specs/015-deployment-hardening/checkpoint.md` |
| 2026-09-13 | #21 016-scenario-runner | evaluation | `measurable` | Web Scenario Runner | gold scenarios passing | — | — | accepted | `evals/runner.py` |
| 2026-09-13 | #22 017-metrics-dashboard | observability | `unmeasured` | Metrics view (latency, tokens, cost, tools) | — | Adds observability; no quality delta measured | — | accepted | `specs/017-metrics-dashboard` |
| 2026-09-13 | #23 chore build-mirrors | deployment | `no-behavior` | Opt-in npm/PyPI build mirrors | — | Build-only; enabled the 015 smoke | — | accepted | `Dockerfile` |
| 2026-09-13 | #24 018-dense-retrieval | retrieval | `measurable` | Dense retrieval behind the Retriever port | hard-query hit-rate@3 | 0.8 → 1.0 | latency ok | accepted | `evals/bench.py` |
| 2026-09-13 | #25 019-skills | agent | `measurable` | Skills catalog + use_skill tool | gold pass rate (ablation) | 0.75 → 0.833 | — | accepted | `evals/ablation.py` |
| 2026-09-13 | #26 020-gates | agent | `no-behavior` | Extract guardrails into app/gates | — | Behavior-preserving refactor | — | accepted | `tests/unit/test_gates.py` |
| 2026-09-13 | #27 021-chroma-vector-store | retrieval | `measurable` | Persistent Chroma vector store | dense-chroma hit-rate@3 | Parity with the in-memory store | — | accepted | `evals/bench.py` |
| 2026-09-13 | #28 022-retrieval-benchmark | evaluation | `measurable` | Keyless retrieval benchmark and ablation | retrieval hit-rate@3 (tfidf -> dense) | 0.963 → 1.0 | — | accepted | `evals/bench.py` |
| 2026-09-13 | #29 023-agent-evaluation | evaluation | `measurable` | Process metrics, attribution, Pass@k/Pass^k, judge, ablation | real Pass@1 | Pass^k 0.667; 0 vetoes | 0 ungrounded | accepted | `evals/report.md` |
| 2026-09-13 | #30 024-parameterized-cases | evaluation | `measurable` | Seeded, harder real-eval cases | real Pass@k | 0.833 → 1.0 | — | accepted | `evals/report.md` |
| 2026-09-13 | #31 025-eval-report-view | web | `no-behavior` | Browser evaluation report view | — | UI view; no metric | — | accepted | `specs/025-eval-report-view` |
| 2026-09-13 | #32 results-in-specs | process | `docs` | Record all key metrics in the specs, gate-checked | — | — | — | accepted | `specs/RESULTS.md` |
| 2026-09-13 | #33 production-constraints | process | `docs` | Constitution RW/SC/EV clauses + production audit | — | — | — | accepted | `docs/production-audit.md` |
| 2026-09-13 | #34 027-change-audit | process | `no-behavior` | Auditable change log + evidence gate + constitution consolidation | — | Tooling/process; no app behavior change | — | accepted | `specs/change-log.json` |
| 2026-09-13 | #35 028-spec-structure | process | `docs` | Normalize the spec structure across all 25 features; complete the spec template | — | — | — | accepted | `.specify/templates/spec-template.md` |
<!-- change-log:end -->
