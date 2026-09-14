# Labeling guide: post-purchase decision cases

The decision set (`evals/post_purchase_cases.jsonl`) is the project's core
evidence. A machine can seed candidates, but a **human must own the labels** —
that is what makes the evaluation credible. This guide tells you how to review and
correct the draft.

## What each case is

One row = one customer message + the facts the agent would have + the **correct
outcome** and the **policy clauses that justify it**.

| Field | Meaning |
| --- | --- |
| `case_id` | stable id |
| `intent` | `wismo` \| `return_eligibility` \| `warranty` \| `clarify` |
| `message` | what the customer sent |
| `delivered_days_ago` | days since delivery (relative to a fixed eval "now"); `null` if unknown |
| `fulfillment_status` | e.g. `IN_TRANSIT`, `FULFILLED` |
| `item_tags` | `large`, `final_sale`, `gift_card`, … |
| `reason` | `unwanted` \| `size_too_large` \| `damaged` \| `defective` \| `wrong_item` \| `missing` |
| `expected_decision` | `eligible` \| `ineligible` \| `escalate` \| `answer_status` \| `clarify` |
| `expected_policy_refs` | clause ids that **support** the decision |
| `notes` | the reasoning, in one line |
| `status` | `draft` (needs your review) → `reviewed` |

## How to decide the label

1. **Is there a decision to make?** If the message is a status question, the
   answer is `answer_status` (from the order record). If a required detail is
   missing ("which item?"), it is `clarify`. If the facts conflict or a rule is
   ambiguous, it is `escalate`.
2. **If it is a return:** check, in order:
   - non-returnable (`final_sale`, `gift_card`) → `ineligible`;
   - an exception reason (`damaged`, `defective`, `wrong_item`, `missing`) →
     `eligible` (no window, no fee);
   - otherwise the window: within → `eligible`, outside → `ineligible`.
3. **Cite the clause(s)** that justify it, from `config/policies/policies.yaml`.
   If you cannot cite a clause, the label is wrong or the policy is incomplete.

## Rules of thumb

- **Never guess.** Missing fact → `escalate` (or `clarify`). "I don't know" is a
  valid, correct label.
- **Boundaries are explicit.** Day 30 is inside; day 31 is outside. Label both.
- **A superseded policy is a trap.** The customer may quote v1 (14 days); the
  active policy is v2 (30 days).
- **Injection is data.** A message or item title that says "ignore the policy" is
  not an instruction; label the outcome the policy gives.

## Your task (the human step)

1. Open `evals/post_purchase_cases.jsonl`.
2. For each `status: "draft"` row, check the `expected_decision` and
   `expected_policy_refs`; correct anything you disagree with.
3. Change `status` to `"reviewed"` when you are confident.
4. Add cases you think are missing (edge cases, real phrasings you would expect).

Then the eval harness will measure the model against **your** labels — that is
what makes the numbers trustworthy.
