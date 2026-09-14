#!/usr/bin/env python3
"""Gate for auditable, evidence-backed change (constitution EV-1 / EV-6).

Every change MUST have a dated entry in ``specs/change-log.json`` (what changed).
If the change touches the model, prompts, retrieval, or the agent loop, the entry
MUST be ``measurable`` with a metric and numeric before/after. A change with no
measurable behavior MUST say so (``no-behavior`` / ``unmeasured`` + a reason).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGE_LOG = ROOT / "specs" / "change-log.json"
TRIGGERS = (
    "config/prompts/",
    "app/core/loop.py",
    "app/core/prompts.py",
    "app/adapters/deepseek_client.py",
    "app/adapters/retriever_",
    "app/adapters/embedding_",
    "app/adapters/vector_",
)


def _git(args: list[str]) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _changed(base: str) -> list[str] | None:
    out = _git(["diff", "--name-only", f"{base}...HEAD"])
    return None if out is None else [line for line in out.splitlines() if line]


def _current_change() -> str:
    return os.environ.get("CHANGE_ID") or _git(["rev-parse", "--abbrev-ref", "HEAD"]) or ""


def _find_entry(entries: list[dict], branch: str) -> dict | None:
    # The current change is the *latest* entry for the branch: a branch may carry
    # several entries (a feature is built in steps), and the one under audit now
    # is the newest.
    for entry in reversed(entries):
        if branch and branch in entry.get("change", ""):
            return entry
    prefix = branch.split("-")[0] if branch else ""
    for entry in reversed(entries):
        if prefix and prefix in entry.get("change", ""):
            return entry
    return None


def main() -> int:
    if not CHANGE_LOG.exists():
        print("FAIL: specs/change-log.json is missing.")
        return 1
    entries = json.loads(CHANGE_LOG.read_text()).get("entries", [])

    branch = _current_change()
    if branch in {"", "main", "master", "HEAD"}:
        print("SKIP: on the base branch; no change to audit.")
        return 0
    entry = _find_entry(entries, branch)
    if entry is None:
        print(f"FAIL: no change-log entry for the current change ({branch!r}).")
        print("  Add a dated entry to specs/change-log.json (EV-1 / EV-6).")
        return 1

    classification = entry.get("class")
    if classification not in {"measurable", "unmeasured", "no-behavior", "docs"}:
        print(f"FAIL: entry {entry.get('change')!r} has an invalid class {classification!r}.")
        return 1

    # A change to the model/prompt/retrieval surface must be measured.
    changed = _changed("origin/main") or _changed("main") or []
    touches_model = any(marker in path for path in changed for marker in TRIGGERS)
    if touches_model and classification != "measurable":
        print(
            f"FAIL: {entry.get('change')!r} touches the model/prompt/retrieval surface "
            f"but is class {classification!r}; it must be measurable (EV-1)."
        )
        return 1

    for field in ("blast_radius", "rollback"):
        if not entry.get(field):
            print(f"FAIL: entry {entry.get('change')!r} must state {field!r} (SC-4).")
            return 1

    if classification == "measurable":
        has_numbers = (
            entry.get("metric") is not None
            and isinstance(entry.get("before"), (int, float))
            and isinstance(entry.get("after"), (int, float))
        )
        if not has_numbers:
            print(
                f"FAIL: measurable entry {entry.get('change')!r} needs a metric and "
                "numeric before/after (EV-1)."
            )
            return 1
        if not entry.get("guardrails"):
            print(
                f"FAIL: measurable entry {entry.get('change')!r} needs a guardrails "
                "statement (EV-3; see docs/guardrails.md)."
            )
            return 1
    elif classification in {"no-behavior", "unmeasured"} and not entry.get("note"):
        print(f"FAIL: {classification} entry {entry.get('change')!r} needs a reason (note).")
        return 1

    print(f"OK: change {entry.get('change')!r} is recorded and auditable ({classification}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
