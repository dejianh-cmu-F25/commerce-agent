#!/usr/bin/env python3
"""Evaluation-set audit (feature 046, Batch F).

An accuracy number is only as good as the corpus behind it. This audits every
corpus the project scores against, keylessly:

1. **Duplicate ids / messages** — a case that appears twice silently double-counts.
2. **Prompt pollution** — a case that is copied from a prompt exemplar measures
   memorisation, not behaviour (CheckList: "negate the test, not the model").
3. **Coverage matrix** — what each corpus actually covers, so a headline number
   cannot be read as covering more than it does.
4. **Sliced results** — the last journey run split by intent and by signal, so
   weak slices cannot hide behind a strong average.

Run::

    uv run python evals/eval_audit.py            # print
    uv run python evals/eval_audit.py --write    # also write reports/eval-audit.md
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "eval-audit.md"
PROMPT_DIR = ROOT / "config" / "prompts"
JOURNEY_RESULTS = ROOT / "evals" / "results-journey.json"
_NGRAM = 8
# ``synth`` is the generator input for the journey corpus, so every synth case
# legitimately reappears in journey; it is not a duplicate defect.
EMBEDDED = {"synth"}


@dataclass
class Case:
    case_id: str
    corpus: str
    text: str
    intent: str = ""


@dataclass
class Audit:
    corpora: dict[str, list[Case]] = field(default_factory=dict)
    duplicate_ids: list[str] = field(default_factory=list)
    duplicate_messages: list[tuple[str, str, str]] = field(default_factory=list)
    polluted: list[tuple[str, str, str]] = field(default_factory=list)
    invariance_pairs: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text).strip()


def _ngrams(text: str, n: int = _NGRAM) -> set[str]:
    words = _normalise(text).split()
    return {" ".join(words[i : i + n]) for i in range(max(0, len(words) - n + 1))}


def _journey_cases() -> list[Case]:
    from evals.journey_eval import build_cases

    return [Case(case.case_id, "journey", case.message, case.intent) for case in build_cases([])]


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _load_corpora() -> dict[str, list[Case]]:
    corpora = {
        "journey": _journey_cases(),
        "synth": [
            Case(row["case_id"], "synth", row["message"], row.get("intent", ""))
            for row in _jsonl(ROOT / "evals" / "synth_cases.jsonl")
        ],
        "post_purchase": [
            Case(row["case_id"], "post_purchase", row.get("message", ""), row["expected_decision"])
            for row in _jsonl(ROOT / "evals" / "post_purchase_cases.jsonl")
        ],
        "invariant": [
            Case(row["case_id"], "invariant", row.get("message", ""), row["invariant"])
            for row in _jsonl(ROOT / "evals" / "invariant_cases.jsonl")
        ],
        "discovery_rule": [
            Case(row["case_id"], "discovery_rule", row["query"], row["rule"])
            for row in _jsonl(ROOT / "evals" / "discovery_cases.jsonl")
        ],
    }
    esci = json.loads((ROOT / "data" / "esci" / "cases.json").read_text())
    corpora["esci"] = [Case(f"esci-{row['query_id']}", "esci", row["query"]) for row in esci]
    return corpora


def _find_duplicates(audit: Audit) -> None:
    seen: dict[str, str] = {}
    for corpus, cases in audit.corpora.items():
        if corpus in EMBEDDED:
            continue
        for case in cases:
            if case.case_id in seen:
                audit.duplicate_ids.append(f"{case.case_id} ({seen[case.case_id]} + {corpus})")
            seen[case.case_id] = corpus

    for corpus, cases in audit.corpora.items():
        if corpus in EMBEDDED:
            continue
        raw: dict[str, list[str]] = {}
        buckets: dict[str, list[str]] = {}
        for case in cases:
            if not case.text:
                continue
            raw.setdefault(case.text, []).append(case.case_id)
            buckets.setdefault(_normalise(case.text), []).append(case.case_id)
        for ids in raw.values():
            if len(ids) > 1:
                audit.duplicate_messages.append((corpus, "within", ", ".join(sorted(ids))))
        # Identical only after case/punctuation folding: the model still sees
        # different bytes, so this is a deliberate invariance pair (CheckList INV),
        # reported separately rather than as a defect.
        exact = {ids[0] for ids in raw.values() if len(ids) > 1}
        for ids in buckets.values():
            if len(ids) > 1 and not set(ids) <= exact:
                audit.invariance_pairs.append((corpus, ", ".join(sorted(ids))))

    names = [name for name in audit.corpora if name not in EMBEDDED]
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            left_text = {c.text: c.case_id for c in audit.corpora[left] if c.text}
            for case in audit.corpora[right]:
                if case.text and case.text in left_text:
                    audit.duplicate_messages.append(
                        (f"{left} x {right}", "across", f"{left_text[case.text]} == {case.case_id}")
                    )
    audit.notes.append(
        "`synth` is the generator input for `journey`, so its cases legitimately reappear "
        "there; it is excluded from the duplicate checks."
    )


def _find_pollution(audit: Audit) -> None:
    prompts = {path.name: _ngrams(path.read_text()) for path in sorted(PROMPT_DIR.glob("*.md"))}
    for corpus, cases in audit.corpora.items():
        for case in cases:
            grams = _ngrams(case.text)
            if not grams:
                continue
            for name, prompt_grams in prompts.items():
                overlap = grams & prompt_grams
                if overlap:
                    audit.polluted.append(
                        (corpus, case.case_id, f"{name}: {' | '.join(sorted(overlap))[:80]}")
                    )


def _slices() -> dict[str, Any]:
    if not JOURNEY_RESULTS.exists():
        return {}
    result = json.loads(JOURNEY_RESULTS.read_text())
    return {
        "model": result.get("model"),
        "cases": result.get("cases"),
        "tool_accuracy": result.get("tool_accuracy"),
        "no_fail_rate": result.get("no_fail_rate"),
        "strong_signal_pass": result.get("strong_signal_pass"),
        "weak_signal_pass": result.get("weak_signal_pass"),
        "pass_4": result.get("pass_4"),
        "by_intent": result.get("by_intent", {}),
        "failures": result.get("failures", []),
    }


def audit() -> Audit:
    result = Audit()
    result.corpora = _load_corpora()
    _find_duplicates(result)
    _find_pollution(result)
    return result


def render(result: Audit) -> str:
    total = sum(len(cases) for cases in result.corpora.values())
    lines = [
        "# Evaluation-set audit",
        "",
        f"- Corpora: **{len(result.corpora)}** · cases: **{total}**",
        "- Checks: duplicate ids/messages, prompt pollution (8-gram), coverage, sliced results.",
        "",
        "## Corpus sizes",
        "",
        "| Corpus | Cases | What it grounds |",
        "| --- | ---: | --- |",
    ]
    grounding = {
        "journey": "end-to-end tool-use behaviour (the headline accuracy)",
        "synth": "novel phrasings of the same intents (CheckList MFT)",
        "post_purchase": "return decisions vs the policy engine",
        "invariant": "behavioural guardrails (INV-1..8)",
        "discovery_rule": "retrieval hit@10 on product metadata",
        "esci": "nDCG@10 against human ESCI relevance labels",
    }
    for name, cases in sorted(result.corpora.items()):
        lines.append(f"| `{name}` | {len(cases)} | {grounding.get(name, '')} |")

    lines += ["", "## Coverage matrix (intent × corpus)", ""]
    intents = sorted(
        {case.intent for cases in result.corpora.values() for case in cases if case.intent}
    )
    lines.append("| Corpus | " + " | ".join(intents) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in intents) + " |")
    for name, cases in sorted(result.corpora.items()):
        counts = Counter(case.intent for case in cases)
        lines.append(
            f"| `{name}` | "
            + " | ".join(str(counts.get(intent, 0) or "") for intent in intents)
            + " |"
        )

    lines += [
        "",
        "## Embedded corpora",
        "",
        "`synth` is excluded from the duplicate checks: it is the generator input for "
        "`journey`, so every synth case reappears there by construction.",
        "",
        "## Duplicate ids",
        "",
    ]
    lines.append(
        "None." if not result.duplicate_ids else "\n".join(f"- {d}" for d in result.duplicate_ids)
    )

    lines += ["", "## Duplicate messages", ""]
    if result.duplicate_messages:
        for where, kind, detail in result.duplicate_messages:
            lines.append(f"- `{where}` ({kind}): {detail}")
    else:
        lines.append("None.")

    lines += ["", "## Invariance pairs (same after case/punctuation folding)", ""]
    if result.invariance_pairs:
        for where, detail in result.invariance_pairs:
            lines.append(f"- `{where}`: {detail}")
    else:
        lines.append("None.")

    lines += ["", "## Prompt pollution (8-gram overlap with config/prompts)", ""]
    lines.append(
        "None — no case shares an 8-word span with a prompt."
        if not result.polluted
        else "\n".join(f"- `{c}` {cid} — {detail}" for c, cid, detail in result.polluted)
    )

    slices = _slices()
    if slices:
        lines += [
            "",
            "## Sliced results (last journey run, real model)",
            "",
            f"- model `{slices['model']}` · cases **{slices['cases']}** · "
            f"tool accuracy **{slices['tool_accuracy']}** · no-fail **{slices['no_fail_rate']}**",
            f"- strong-signal **{slices['strong_signal_pass']}** · "
            f"weak-signal **{slices['weak_signal_pass']}** · Pass^4 **{slices['pass_4']}**",
            "",
            "| Intent | Passed |",
            "| --- | ---: |",
        ]
        for intent, value in sorted(slices["by_intent"].items()):
            lines.append(f"| `{intent}` | {value} |")
        if slices["failures"]:
            lines += ["", f"**Failures:** {', '.join(slices['failures'])}"]

    lines += ["", "## Notes", ""] + [f"- {note}" for note in result.notes] + [""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    text = render(result)
    print(text)
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(text)
        print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
