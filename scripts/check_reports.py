#!/usr/bin/env python3
"""Fail when a report no longer matches the corpus it describes (feature 046).

Reports drifted silently three times in one session and each time the numbers looked
plausible: a guardrail row outlived its metric, a journey report quoted a failure that
had been fixed, an audit predated a corpus it claimed to cover. Reviewers (and agents)
read these files as evidence, so a stale one is worse than a missing one.

Every report carries a ``report-meta`` line naming its generator, its case count and
the source files that define the corpus, with a content fingerprint of those files.
This recomputes the fingerprint and fails on a mismatch, so the gate refuses a report
whose corpus has moved underneath it.

Run::

    uv run python scripts/check_reports.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.evaluation.report_meta import file_fingerprint, parse  # noqa: E402

REPORTS = ROOT / "reports"
GATED = sorted(REPORTS.glob("*.md")) + [ROOT / "evals" / "report.md"]


def check() -> list[str]:
    failures: list[str] = []
    for path in GATED:
        relative = path.relative_to(ROOT)
        if not path.exists():
            failures.append(f"{relative}: missing")
            continue
        meta = parse(path.read_text())
        if meta is None:
            failures.append(
                f"{relative}: no report-meta line (a report must state its generator, "
                "cases, sources and fingerprint)"
            )
            continue
        actual = file_fingerprint(list(meta.sources))
        if actual != meta.fingerprint:
            failures.append(
                f"{relative}: STALE - its corpus changed since it was written "
                f"(fingerprint {meta.fingerprint} -> {actual}); "
                f"re-run `{meta.generator}`"
            )
    return failures


def main() -> int:
    failures = check()
    if failures:
        print(f"FAIL: {len(failures)} report(s) unverified or stale")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"OK: {len(GATED)} reports match the corpus they describe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
