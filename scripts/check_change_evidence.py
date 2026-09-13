#!/usr/bin/env python3
"""Gate for evidence-backed change (constitution EV-1, v1.3.0).

If a change touches the model, prompts, retrieval, or the agent loop, it must
update the evaluation evidence (``evals/report.md`` or ``specs/RESULTS.md``).
Compares the current branch against ``origin/main`` (falling back to ``main``);
when no base is available it skips rather than blocking.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ("evals/report.md", "specs/RESULTS.md")
TRIGGERS = (
    "config/prompts/",
    "app/core/loop.py",
    "app/core/prompts.py",
    "app/adapters/deepseek_client.py",
    "app/adapters/retriever_",
    "app/adapters/embedding_",
    "app/adapters/vector_",
)


def _changed(base: str) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [line for line in result.stdout.splitlines() if line]


def _triggers(changed: list[str]) -> list[str]:
    return [path for path in changed if any(marker in path for marker in TRIGGERS)]


def main() -> int:
    changed = _changed("origin/main")
    if changed is None:
        changed = _changed("main")
    if changed is None:
        print("SKIP: no git base to compare (expected origin/main or main).")
        return 0

    triggering = _triggers(changed)
    if not triggering:
        print("OK: no model/prompt/retrieval change; no evidence required.")
        return 0

    if any(path in EVIDENCE for path in changed):
        print("OK: change evidence updated alongside the model/prompt/retrieval change.")
        return 0

    print("FAIL: this change touches the model/prompt/retrieval surface but updates no evidence.")
    print("  Triggering files:", ", ".join(triggering[:6]))
    print(
        f"  Add before/after evidence to one of: {', '.join(EVIDENCE)} "
        "(EV-1; docs/production-conventions.md)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
