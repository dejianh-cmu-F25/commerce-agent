#!/usr/bin/env python3
"""Gate for measured results and the change log (constitution P1, P7, EV).

- Verifies the keyless numbers in ``evals/report.md`` match the freshly generated
  artifacts (``evals/results-keyless.json``).
- Verifies every ``specs/change-log.json`` entry is well-formed: a ``measurable``
  entry carries a metric and a result (``after``).

Real-model numbers are dated snapshots and are not checked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "evals" / "results-keyless.json"
REPORT = ROOT / "evals" / "report.md"
CHANGE_LOG = ROOT / "specs" / "change-log.json"

RETRIEVAL_HEADING = "## Retrieval benchmark"
ABLATION_HEADING = "## Feature ablation"
SEGMENTS_HEADING = "## Segmented metrics"
DATA_QUALITY_HEADING = "## Data quality"
ADVERSARIAL_HEADING = "## Adversarial input"
SCALE_HEADING = "## Scale & SLOs"
REQUIRED_FIELDS = ("date", "change", "area", "class", "what", "verdict", "evidence")
VALID_CLASSES = {"measurable", "unmeasured", "no-behavior", "docs"}


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _row(section: str, config: str) -> list[str] | None:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"| `{config}` |"):
            return [cell.strip() for cell in stripped.strip("|").split("|")]
    return None


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _check_report(artifacts: dict) -> list[str]:
    failures: list[str] = []
    if not REPORT.exists():
        return ["evals/report.md is missing"]
    text = REPORT.read_text()

    retrieval = artifacts.get("retrieval", {})
    if retrieval:
        section = _section(text, RETRIEVAL_HEADING)
        if not section:
            failures.append("report.md has no retrieval section")
        for config, metrics in retrieval["configs"].items():
            row = _row(section, config)
            if row is None:
                failures.append(f"retrieval row for {config!r} missing")
                continue
            expected = [
                f"{metrics['hit_rate']:.3f}",
                f"{metrics['recall']:.3f}",
                f"{metrics['mrr']:.3f}",
            ]
            if row[1:4] != expected:
                failures.append(f"retrieval {config}: {row[1:4]} != {expected}")

    ablation = artifacts.get("ablation", {})
    if ablation:
        section = _section(text, ABLATION_HEADING)
        if not section:
            failures.append("report.md has no ablation section")
        for config, metrics in ablation["configs"].items():
            row = _row(section, config)
            if row is None:
                failures.append(f"ablation row for {config!r} missing")
                continue
            expected = f"{metrics['pass_rate']:.3f}"
            if row[2] != expected:
                failures.append(f"ablation {config}: pass rate {row[2]} != {expected}")

    segments = artifacts.get("segments", {})
    if segments.get("by_intent"):
        section = _section(text, SEGMENTS_HEADING)
        if not section:
            failures.append("report.md has no segmented-metrics section")
        else:
            for intent, metrics in segments["by_intent"].items():
                expected = (
                    f"| `{intent}` | {metrics['passed']:.0f}/{metrics['total']:.0f} | "
                    f"{metrics['pass_rate']:.3f} |"
                )
                if expected not in section:
                    failures.append(f"segments: expected intent row {expected!r} in the report")

    data_quality = artifacts.get("data_quality", {})
    if data_quality:
        section = _section(text, DATA_QUALITY_HEADING)
        if not section:
            failures.append("report.md has no data-quality section")
        else:
            expected = (
                f"| {data_quality['cases']} | "
                f"{data_quality.get('baseline_accuracy', 0.0):.3f} | "
                f"{data_quality['accuracy']:.3f} |"
            )
            if expected not in section:
                failures.append(f"data quality: expected row {expected!r} in the report")

    adversarial = artifacts.get("adversarial", {})
    if adversarial:
        section = _section(text, ADVERSARIAL_HEADING)
        if not section:
            failures.append("report.md has no adversarial section")
        else:
            expected = (
                f"| {adversarial['cases']} | "
                f"{adversarial.get('baseline_safe_rate', 0.0):.3f} | "
                f"{adversarial['safe_rate']:.3f} |"
            )
            if expected not in section:
                failures.append(f"adversarial: expected row {expected!r} in the report")

    # Scale numbers are wall-clock timings, not reproducible run to run; check
    # that the section and the target row exist, not their exact values. The SLO
    # budget itself is enforced by evals/scale.py (SC-3).
    scale = artifacts.get("scale", {})
    if scale and scale.get("levels"):
        section = _section(text, SCALE_HEADING)
        if not section:
            failures.append("report.md has no scale section")
        else:
            target = scale["envelope"]["target_concurrency"]
            if f"| {target} |" not in section:
                failures.append(f"scale: no row for concurrency {target}")
    return failures


def _check_change_log() -> list[str]:
    failures: list[str] = []
    if not CHANGE_LOG.exists():
        return ["specs/change-log.json is missing"]
    entries = json.loads(CHANGE_LOG.read_text()).get("entries", [])
    if not entries:
        return ["specs/change-log.json has no entries"]
    for entry in entries:
        name = entry.get("change", "?")
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                failures.append(f"change-log {name!r}: missing {field!r}")
        classification = entry.get("class")
        if classification not in VALID_CLASSES:
            failures.append(f"change-log {name!r}: invalid class {classification!r}")
        if classification == "measurable" and (
            entry.get("metric") is None or entry.get("after") is None
        ):
            failures.append(f"change-log {name!r}: measurable entry needs metric + after")
    return failures


def main() -> int:
    artifacts = _load(ARTIFACTS)
    failures: list[str] = []
    if artifacts:
        failures += _check_report(artifacts)
    else:
        print("SKIP: no keyless artifacts yet (run evals/bench.py and evals/ablation.py).")
    failures += _check_change_log()

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: report.md matches the keyless artifacts; the change log is well-formed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
