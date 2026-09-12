# Agent Note: Evaluation separates capability, reliability, and process

Status: implemented (2026-09-13) — feature `023-agent-evaluation`

## Problem

The eval harness measured end-to-end pass/fail on scripted scenarios but could
not answer the questions an interviewer (or a resume) asks: How reliable is it
across runs? Where does it fail? What did each feature contribute? Is the answer
grounded? Following the book's chapter 7, the project needed Pass@k / Pass^k,
process metrics, failure attribution, a rubric judge, and a feature ablation.

## Alternatives considered

- **Keep only end-to-end pass/fail.** Simple, but says nothing about reliability,
  cause, or per-feature contribution. Rejected.
- **Judge everything with an LLM.** Convenient, but nondeterministic and it makes
  the gate depend on a key. Rejected: deterministic metrics first; the judge is
  opt-in and has a rule-based fallback.
- **Run real models in the gate.** Realistic, but slow, costly, and
  nondeterministic. Rejected: the gate runs the keyless ablation; real runs are
  opt-in and budget-capped.
- **A different judge family.** Avoids same-source bias, but needs another key.
  Deferred: DeepSeek is the judge, the bias is documented, and the judge model is
  configurable.

## Decision

- **Separate metrics.** Pass@1 / Pass@k / Best@k / Pass^k
  (`app/evaluation/reliability.py`); process metrics from spans
  (`agent_metrics.py`); first-error attribution (`failure.py`).
- **A rubric judge with a veto.** `app/evaluation/rubric.py` scores grounding,
  correctness, policy compliance, completeness, and tone, and vetoes any
  fabricated price/stock/policy fact (the grounding rule, P4). Malformed judge
  output falls back to deterministic checks (RD-1). The prompt is external
  (`config/prompts/judge.md`, PB-4).
- **A keyless feature ablation.** `evals/ablation.py` runs the gold scenarios
  under naked / +memory / +skills / retrieval configs and reports the delta vs the
  naked baseline — the "I changed X → effect Y" evidence.
- **Opt-in, budget-capped real runs.** `evals/agent_eval.py --real` runs the real
  agent over outcome-based cases × seeds, computes reliability/process/attribution
  and the judge, and stops at `evaluation.max_cost_cny` (HR-12).
- **A committed report.** `evals/report.py` merges the keyless and real sections
  into `evals/report.md`; a keyless run never clobbers real numbers.

## Consequences

- The report now carries evidence: memory +0.167, skills +0.083 on the gold set;
  dense retrieval closes the hard-query gap (0.80 → 1.00); a real DeepSeek run
  reported Pass@1/Pass@k/Pass^k = 1.000 over 21 runs at CNY 0.0908, 0 ungrounded
  attempts, and 0 judge vetoes.
- **Same-source bias:** the agent and judge are both DeepSeek; per the book, a
  same-family judge can share blind spots. The bias is recorded, and
  `evaluation.judge_model` allows a different model.
- Perfect scores mean the case set is easy for the current model; harder,
  parameterized cases are the next step to make the metric discriminate.
- Real runs spend budget and are never part of the gate; the keyless ablation is.
- The loop now closes its provider stream deterministically, removing an async
  cleanup error seen during real runs (RD-1).
