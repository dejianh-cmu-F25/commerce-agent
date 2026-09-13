# Production Conventions

Guide for the clauses **RW (Real-World Fitness)**, **SC (Scale & Operability)**,
and **EV (Evidence-Backed Change)** in the constitution (v1.3.0). This is the
sibling of `docs/ui-conventions.md`: the constitution states the rule, this file
holds the detail and the review checklist.

The goal is simple: this project must be **genuinely useful**, not a demo that
collapses under real traffic. That means covering real phrasing and dirty data,
defining boundaries instead of discovering them, being diagnosable at scale, and
proving that every change improved things.

## Writing the `## Real-World Coverage` section

A feature that interprets free-form input, handles data, or changes the
model / prompt / retrieval / modules must fill in `## Real-World Coverage` in its
spec. Keep each item concrete and testable.

- **Input distribution.** List the real inputs (phrasings, ambiguity, languages,
  adversarial). Say what the system does with input it has not seen — ask a
  clarifying question, refuse, or fall back. "The user asks nicely" is not a
  distribution.
- **Data quality.** State where data enters, what is validated and normalized,
  and what happens with missing, dirty, or conflicting data. Every assumption
  about an upstream system is a liability; make it explicit and checked.
- **Edge & failure modes.** Enumerate them and give each a defined behavior. An
  undefined boundary is a defect (RW-3), not a surprise.
- **Scale envelope.** Name the dimensions that matter (traffic, data volume,
  concurrency, tenancy, session length) and the boundary you measured. For a solo
  project the bar is "declared and measured at the stated boundary", not a
  production load test.
- **Degradation.** For each external dependency, the fallback and how the
  degraded state is surfaced (observable, never silent).
- **Change evidence.** For a model / prompt / retrieval / module change, the
  before/after numbers and where they live.

## Recording change evidence (EV)

A change to the model, a prompt, retrieval, or a module is **not done** without a
before/after record in `specs/RESULTS.md` / `evals/report.md`.

- **Paired, not averaged.** Run the same tasks with the same seeds for both
  configurations and compare per task. `evals/agent_eval.py` and the ablation
  already do this; report the effect size and the sample size.
- **Guardrails first.** Quality, safety (zero ungrounded writes), latency, and
  cost are guardrails. If the target improves but a guardrail regresses, the
  change is rejected.
- **Version it.** Record the model and a hash of the rendered system prompt with
  the results (`evals/report.md`).
- **Regressions from reality.** When something fails in real use, add it as an
  end-to-end and, where useful, a trajectory-prefix regression case.

## Review checklist

Reviewer-owned. Mark an item only when verified.

### Real-world fitness (RW)
- [ ] The input distribution is enumerated, including adversarial and out-of-distribution input.
- [ ] Unseen input has a defined behavior (clarify / refuse / fall back), not an implicit assumption.
- [ ] Data boundaries validate and normalize; dirty/missing/conflicting data has defined behavior and a repair path.
- [ ] Edge and failure modes are enumerated with a behavior each.
- [ ] Fixes address the root cause and ship with a regression; no one-off special cases.
- [ ] Every external dependency has a config-gated, observable fallback.

### Scale & operability (SC)
- [ ] The scale envelope is declared and measured at the stated boundary.
- [ ] Failures are attributable (trace + first error); metrics are segmentable (intent / tool / model / tenant).
- [ ] Latency, cost, and error budgets are declared and tracked.
- [ ] The change is localized behind seams; blast radius and rollback/migration are stated.

### Evidence-backed change (EV)
- [ ] Model / prompt / retrieval / module changes have a before/after evaluation on a fixed benchmark.
- [ ] The comparison is paired with multiple seeds; effect size and sample size are reported.
- [ ] Guardrail metrics did not regress.
- [ ] The model and rendered-prompt hash are recorded with the results.
- [ ] Production failures became regression cases.

## Sources

- The project's `ai-agent-book`, chapter 7, *Evaluating Agents* (metrics,
  failure attribution, rubric judging, ablation, model selection, cost).
- Google SRE, *Service Level Objectives* (error budgets).
- The constitution, clauses RW / SC / EV (v1.3.0).
