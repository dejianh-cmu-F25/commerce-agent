#!/usr/bin/env python3
"""Synthesise diverse phrasings for the journey eval (feature 046, Batch C).

The old corpora reuse a handful of templates, so a high pass rate proves little.
This asks an LLM for **many different ways** a real user would say the same thing
(CheckList MFT), and for **paraphrases** of existing cases (CheckList INV: the
intent is unchanged, so the expected tool must not change). The result is cached
to ``evals/synth_cases.jsonl`` (committed) so runs are reproducible.

Run::

    uv run python evals/synth_cases.py --per-intent 6
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals" / "synth_cases.jsonl"

SEEDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("discovery", "find a lightweight tent for summer camping under $200", ("search_products",)),
    ("discovery", "looking for wireless earbuds under $50", ("search_products",)),
    ("policy", "how long do I have to return something?", ("search_knowledge",)),
    ("policy", "who pays for return shipping?", ("search_knowledge",)),
    (
        "return",
        "I want to return the item from order #1006 because it did not fit",
        ("propose_return_decision",),
    ),
    ("wismo", "where is my order #1006?", ("get_order_status",)),
]

PROMPT = """You generate realistic ways a customer would phrase a request to an
online-store assistant. Keep the SAME intent; vary wording, length, politeness,
and word order. No two may be near-duplicates. Do not add new constraints.

Intent category: {intent}
Original phrasing: {seed}

Return a JSON array of {n} strings only."""


async def _generate(intent: str, seed: str, n: int) -> list[str]:
    from app.adapters.deepseek_client import DeepSeekClient
    from app.core.settings import load_settings
    from app.core.types import Message

    settings = load_settings()
    llm = DeepSeekClient(settings.llm)
    messages = [Message(role="user", content=PROMPT.format(intent=intent, seed=seed, n=n))]
    text = ""
    async for event in llm.stream(messages, []):  # type: ignore[arg-type]
        delta = getattr(event, "text", None)
        if delta:
            text += delta
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < 0:
        return []
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if isinstance(item, str)]


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-intent", type=int, default=6)
    args = parser.parse_args()

    cases: list[dict] = []
    seen: set[str] = set()
    for seed_index, (intent, seed, tools) in enumerate(SEEDS, 1):
        phrases = await _generate(intent, seed, args.per_intent)
        kept = 0
        for phrase in phrases:
            key = phrase.strip().lower()
            if key in seen or key == seed.lower():
                continue
            seen.add(key)
            cases.append(
                {
                    "case_id": f"synth-{seed_index:02d}-{kept:02d}",
                    "intent": intent,
                    "message": phrase.strip(),
                    "expect_tools": list(tools),
                    "source": "synthetic",
                }
            )
            kept += 1
        print(f"  {intent}: {kept} novel phrasings", flush=True)

    OUT.write_text("\n".join(json.dumps(case) for case in cases) + "\n")
    unique = len({c["message"].strip().lower() for c in cases})
    print(f"wrote {OUT}  cases={len(cases)} unique={unique}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
