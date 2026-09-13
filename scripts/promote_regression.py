#!/usr/bin/env python3
"""Promote a failure into the regression registry (feature 033, RW-4/EV-5).

A regression without a root cause is a symptom, not a fix: promotion refuses an
entry with an empty root cause. Idempotent by id (RD-2).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "evals" / "regressions.json"


def promote(registry_path: str | Path, entry: dict) -> str:
    """Add or update a regression entry; return 'added' or 'updated'."""
    if not str(entry.get("root_cause", "")).strip():
        raise ValueError("a regression requires a root cause (RW-4)")
    for field in ("id", "source", "check"):
        if not str(entry.get(field, "")).strip():
            raise ValueError(f"a regression requires {field!r}")

    path = Path(registry_path)
    data = json.loads(path.read_text()) if path.exists() else {"regressions": []}
    regressions = data.setdefault("regressions", [])
    for index, existing in enumerate(regressions):
        if existing.get("id") == entry["id"]:
            regressions[index] = entry
            action = "updated"
            break
    else:
        regressions.append(entry)
        action = "added"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return action


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a failure into the regression registry.")
    parser.add_argument("--id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--root-cause", required=True)
    parser.add_argument("--check", required=True, help="a named check in evals/regressions.py")
    args = parser.parse_args()
    try:
        action = promote(
            REGISTRY,
            {
                "id": args.id,
                "source": args.source,
                "root_cause": args.root_cause,
                "check": args.check,
            },
        )
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"{action} regression {args.id!r} (check {args.check!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
