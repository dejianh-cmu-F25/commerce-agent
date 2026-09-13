"""Keyless guardrail aggregation (feature 036, EV-3).

Reads the keyless artifacts, compares each guardrail metric to its declared floor
(`docs/guardrails.md`), and fails the gate on a regression. It aggregates rather
than recomputes, so it cannot disagree with the report and costs nothing (P8).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYLESS = ROOT / "evals" / "results-keyless.json"
BUDGET = ROOT / "data" / "budget.json"
HISTORY = ROOT / "evals" / "guardrail-history.jsonl"
HISTORY_LIMIT = 50


@dataclass(frozen=True)
class Guardrail:
    name: str
    value: float
    floor: float
    direction: str  # "at_least" | "at_most"
    source: str

    @property
    def ok(self) -> bool:
        if self.direction == "at_least":
            return self.value >= self.floor
        return self.value <= self.floor


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def evaluate(keyless: dict, budget: dict) -> list[Guardrail]:
    guardrails: list[Guardrail] = []

    def add(name: str, value: float, floor: float, direction: str, source: str) -> None:
        guardrails.append(Guardrail(name, round(float(value), 4), floor, direction, source))

    segments = keyless.get("segments", {}).get("by_intent", {})
    if segments:
        passed = sum(metrics["passed"] for metrics in segments.values())
        total = sum(metrics["total"] for metrics in segments.values())
        add("quality:gold_pass_rate", passed / total if total else 0.0, 1.0, "at_least", "segments")

    adversarial = keyless.get("adversarial", {})
    if adversarial:
        add(
            "safety:adversarial_safe_rate",
            adversarial["safe_rate"],
            1.0,
            "at_least",
            "adversarial",
        )
    regressions = keyless.get("regressions", {})
    if regressions:
        add(
            "safety:regression_coverage",
            regressions["coverage"],
            1.0,
            "at_least",
            "regressions",
        )
    data_quality = keyless.get("data_quality", {})
    if data_quality:
        add("data:dirty_accuracy", data_quality["accuracy"], 1.0, "at_least", "data_quality")
    fallbacks = keyless.get("fallbacks", {})
    if fallbacks:
        add(
            "resilience:fallback_coverage",
            fallbacks["coverage"],
            1.0,
            "at_least",
            "fallbacks",
        )

    scale = keyless.get("scale", {})
    if scale.get("levels"):
        target = scale["envelope"]["target_concurrency"]
        level = next((item for item in scale["levels"] if item["concurrency"] == target), None)
        if level:
            add(
                "latency:turn_p95_us",
                level["turn"]["p95_us"],
                scale["slo"]["turn_p95_us"],
                "at_most",
                "scale",
            )

    spent = budget.get("spent_cny")
    if spent is not None:
        add("cost:spent_cny", spent, 10.0, "at_most", "budget")

    return guardrails


def load_history(path: Path = HISTORY) -> list[dict]:
    """Read the committed guardrail history (one JSON object per line)."""
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            entries.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return entries


def record(result: dict, path: Path = HISTORY, limit: int = HISTORY_LIMIT) -> None:
    """Append the current guardrail values to the committed history (EV-3)."""
    history = load_history(path)
    history.append(
        {
            "date": datetime.now(UTC).date().isoformat(),
            "metrics": {metric["name"]: metric["value"] for metric in result["metrics"]},
        }
    )
    history = history[-limit:]
    path.write_text("\n".join(json.dumps(entry) for entry in history) + "\n")


def run_guardrails() -> dict:
    keyless = _load(KEYLESS)
    guardrails = evaluate(keyless, _load(BUDGET))
    history = load_history()
    previous = history[-1]["metrics"] if history else {}
    metrics: list[dict] = []
    for guardrail in guardrails:
        row = asdict(guardrail) | {"ok": guardrail.ok}
        prior = previous.get(guardrail.name)
        row["previous"] = prior
        row["delta"] = round(guardrail.value - prior, 4) if prior is not None else None
        metrics.append(row)
    failures = [g.name for g in guardrails if not g.ok]
    return {"metrics": metrics, "ok": not failures, "failures": failures}


def write_keyless(result: dict) -> None:
    data = _load(KEYLESS)
    data["guardrails"] = result
    KEYLESS.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate and check guardrails.")
    parser.add_argument(
        "--record", action="store_true", help="append the current values to the history"
    )
    args = parser.parse_args()

    result = run_guardrails()
    print(f"guardrails ({len(result['metrics'])} metrics)")
    for metric in result["metrics"]:
        symbol = ">=" if metric["direction"] == "at_least" else "<="
        status = "OK" if metric["ok"] else "FAIL"
        delta = f"Δ{metric['delta']:+.4f}" if metric["delta"] is not None else "Δ—"
        print(
            f"  {status:<4} {metric['name']:<32} {metric['value']} {symbol} {metric['floor']}"
            f"  {delta}  ({metric['source']})"
        )
    write_keyless(result)
    if args.record:
        record(result)
        print(f"recorded to {HISTORY.relative_to(ROOT)}")
    if not result["ok"]:
        print(f"FAIL: guardrail regression: {result['failures']}")
        return 1
    print("OK: all guardrails within floors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
