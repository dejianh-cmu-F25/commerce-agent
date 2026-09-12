---
name: spec-review
description: Self-review the current work against the project constitution and the feature spec, then write a compliance report. Use before opening a pull request, or when the user says "self-review", "check compliance", "review against spec", "自审", or "检查是否符合规范".
---

# Spec Review

Check the change against **every clause of the constitution** and the feature
spec, then record the result. This is the gate that makes "complies with the
specification" machine-checked rather than a matter of trust (SR-1..SR-3).

## Pipeline

```
Identify feature -> Run the checker -> Address failures -> Confirm manual clauses
```

### 1. Identify the feature

Use the current branch name (`<NNN>-<name>`) as the feature id. If the branch is
not a feature branch, ask which feature is under review.

### 2. Run the checker

```sh
python scripts/spec_review.py <NNN>-<name>
```

This writes `specs/<NNN>-<name>/review.md` and exits non-zero if any clause
FAILs.

### 3. Address failures

If the checker reports a FAIL, fix the cause. **Do not open a pull request while
a clause fails without a recorded waiver** (SR-3).

### 4. Confirm the manual clauses

Read each `MANUAL` row in `review.md` and record a one-line conclusion in the
report. A manual clause is not "done" until it has a conclusion. Typical manual
clauses: contract-first usage, explicit boundaries, prompts external, validation
at boundaries, guides and sensors, GitHub workflow.

### 5. Report

Summarize the result to the user: counts of AUTO / MANUAL / FAIL, and any
waivers with reasons. Then hand off to `feature-close`.
