"""Keyless data-quality benchmark (feature 027, RW-2).

Scores the boundary normalizers against a labeled dirty-input set and writes the
result to ``evals/results-keyless.json`` (regenerated, not committed). The gate
runs this and fails below the threshold.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.data.quality import clean_text, normalize_product, parse_price, parse_stock, parse_tags
from evals.data_quality_set import DATA_QUALITY_SET

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"
MIN_ACCURACY = 1.0


def _actual(kind: str, raw: Any) -> Any:
    if kind == "clean_text":
        return clean_text(raw)
    if kind == "parse_price":
        return parse_price(raw)
    if kind == "parse_stock":
        return parse_stock(raw)
    if kind == "parse_tags":
        return parse_tags(raw)
    if kind == "normalize_product":
        product = normalize_product(raw)
        if product is None:
            return None
        return (product.id, product.title, product.price, product.stock, product.tags)
    raise ValueError(f"unknown case kind: {kind}")


def _naive(kind: str, raw: Any) -> Any:
    """The pre-027 boundary behavior (no validation), for a before/after baseline."""
    try:
        if kind == "clean_text":
            return str(raw)
        if kind == "parse_price":
            return float(raw)
        if kind == "parse_stock":
            return int(raw)
        if kind == "parse_tags":
            return [tag for tag in str(raw).split(",") if tag]
        if kind == "normalize_product":
            return (
                str(raw["id"]),
                str(raw["title"]),
                float(raw["price"]),
                int(raw["stock"]),
                [tag for tag in str(raw.get("tags", "")).split(",") if tag],
            )
    except (TypeError, ValueError, KeyError):
        return "__error__"
    return "__error__"


def run_data_quality() -> dict:
    passed = 0
    naive_passed = 0
    failures: list[str] = []
    for case in DATA_QUALITY_SET:
        actual = _actual(case.kind, case.raw)
        if actual == case.expected:
            passed += 1
        else:
            failures.append(f"{case.kind}({case.raw!r}) -> {actual!r} != {case.expected!r}")
        if _naive(case.kind, case.raw) == case.expected:
            naive_passed += 1
    total = len(DATA_QUALITY_SET)
    return {
        "cases": total,
        "passed": passed,
        "accuracy": round(passed / total, 4) if total else 0.0,
        "baseline_passed": naive_passed,
        "baseline_accuracy": round(naive_passed / total, 4) if total else 0.0,
        "failures": failures,
    }


def write_keyless(result: dict) -> None:
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["data_quality"] = result
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    result = run_data_quality()
    print(f"data quality ({result['cases']} labeled cases)")
    print(f"  before (naive)={result['baseline_accuracy']:.3f}")
    print(f"  after (normalized)={result['accuracy']:.3f}  ({result['passed']}/{result['cases']})")
    for failure in result["failures"]:
        print(f"  FAIL {failure}")
    write_keyless(result)
    if result["accuracy"] < MIN_ACCURACY:
        print(f"FAIL: accuracy below {MIN_ACCURACY}")
        return 1
    print(f"OK: accuracy >= {MIN_ACCURACY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
