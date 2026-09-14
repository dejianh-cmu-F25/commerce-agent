#!/usr/bin/env python3
"""Self-review: check the codebase against the constitution (SR-1..SR-3).

Runs the checks that can be automated and marks the rest MANUAL. Writes
``specs/<NNN>-<name>/review.md`` and exits non-zero if any clause FAILs, so it
can gate a pull request in CI.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SPECS = ROOT / "specs"

PASS, FAIL, MANUAL, NA = "AUTO", "FAIL", "MANUAL", "N/A"


@dataclass
class Result:
    clause: str
    status: str
    evidence: str


def _read_tree(path: Path) -> str:
    if not path.exists():
        return ""
    return "\n".join(p.read_text(errors="ignore") for p in path.rglob("*.py"))


APP_TEXT = _read_tree(APP)


def _has(pattern: str) -> bool:
    return re.search(pattern, APP_TEXT, re.I) is not None


def _absent(pattern: str) -> bool:
    return not _has(pattern)


# Terms that indicate a feature touches free-form input, data, the model, or
# retrieval — the trigger for the Real-World Coverage requirement (RW).
_RW_MARKERS = (
    "tool",
    "retriev",
    "model",
    "prompt",
    "knowledge",
    "memory",
    "llm",
    "order",
    "cart",
    "policy",
    "input",
    "data",
)


def _requires_coverage(spec_md: str) -> bool:
    lowered = spec_md.lower()
    return any(marker in lowered for marker in _RW_MARKERS)


# The six bullets every `## Real-World Coverage` section must carry, with content
# (RW-3: enumerate the boundaries, do not just name the section).
_COVERAGE_BULLETS = (
    "Input distribution",
    "Data quality",
    "Edge & failure modes",
    "Scale envelope",
    "Degradation",
    "Change evidence",
)


def _coverage_gaps(spec_md: str) -> list[str]:
    match = re.search(r"^## Real-World Coverage\s*$(.*?)(?=^## |\Z)", spec_md, re.S | re.M)
    block = match.group(1) if match else ""
    gaps: list[str] = []
    for bullet in _COVERAGE_BULLETS:
        found = re.search(rf"\*\*{re.escape(bullet)}\*\*:\s*(.+)", block)
        if found is None:
            gaps.append(bullet)
            continue
        content = found.group(1).strip()
        # A short bullet is allowed only as an *explained* "n/a (reason)".
        if len(content) < 10 and not re.match(r"n/?a\s*\(.+\)", content, re.I):
            gaps.append(f"{bullet} (too short)")
    return gaps


def _latest_spec() -> Path | None:
    if not SPECS.exists():
        return None
    dirs = sorted(p for p in SPECS.iterdir() if p.is_dir() and re.match(r"^\d+", p.name))
    return dirs[-1] if dirs else None


def _branch_spec() -> Path | None:
    """The spec for the current git branch (``NNN-*``), if there is one.

    The gate must review the *feature under construction*, not whatever spec
    happens to have the highest number.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    match = re.match(r"^(\d+)-", out.stdout.strip())
    if not match or not SPECS.exists():
        return None
    prefix = match.group(1)
    for path in sorted(SPECS.iterdir()):
        if path.is_dir() and path.name.startswith(f"{prefix}-"):
            return path
    return None


def _requires_hitl(spec_md: str) -> bool:
    lowered = spec_md.lower()
    return any(
        marker in lowered
        for marker in ("propose", "approve", "refund", "human-in-the-loop", "human approval")
    )


def _requires_provenance(spec_md: str) -> bool:
    lowered = spec_md.lower()
    return any(
        marker in lowered
        for marker in ("license", "shopify", "esci", "public policy", "external data")
    )


def _tasks_complete(spec: Path) -> tuple[bool, str]:
    tasks = spec / "tasks.md"
    if not tasks.exists():
        return False, "no tasks.md"
    text = tasks.read_text()
    open_tasks = len(re.findall(r"^- \[ \]", text, re.M))
    done = len(re.findall(r"^- \[x\]", text, re.M))
    if open_tasks:
        return False, f"{open_tasks} open task(s)"
    return True, f"{done} task(s) complete"


def check(spec: Path) -> list[Result]:
    results: list[Result] = []

    # --- Core principles ---
    spec_exists = spec.exists()
    tasks_ok, tasks_ev = _tasks_complete(spec) if spec_exists else (False, "no spec dir")
    results.append(
        Result(
            "P1 spec is the source of truth", PASS if spec_exists and tasks_ok else FAIL, tasks_ev
        )
    )
    results.append(
        Result(
            "P2 one agent, skills, tools",
            PASS if _absent(r"subagent|multi_agent|orchestrator_workers") else FAIL,
            "no multi-agent orchestration in app/",
        )
    )
    results.append(
        Result(
            "P3 model proposes, harness disposes",
            PASS if _absent(r"def\s+(charge|capture_payment|place_order)\b") else FAIL,
            "no charge/place-order code in app/",
        )
    )
    results.append(
        Result("P4 grounding", PASS if _has(r"provenance") else FAIL, "provenance tracked")
    )
    results.append(Result("P5 contract first", MANUAL, "ports exist; confirm consumers use them"))

    # --- Ports & boundaries ---
    ports = list((APP / "ports").glob("*.py")) if (APP / "ports").exists() else []
    results.append(
        Result(
            "PB-1 config as contract",
            PASS
            if _absent(r"api\.deepseek\.com") and (ROOT / "config/settings.yaml").exists()
            else FAIL,
            "no hardcoded endpoint in app/; settings.yaml present",
        )
    )
    results.append(
        Result("PB-2 capability seam", PASS if ports else FAIL, f"{len(ports)} port module(s)")
    )
    results.append(
        Result("PB-3 explicit boundaries", MANUAL, "confirm resolve/run split where defaulting")
    )
    prompts = (
        list((ROOT / "config/prompts").glob("*.md")) if (ROOT / "config/prompts").exists() else []
    )
    results.append(
        Result(
            "PB-4 prompts external",
            PASS if prompts and _absent(r'"""[\s\S]{300,}"""') else MANUAL,
            f"{len(prompts)} prompt file(s)",
        )
    )
    results.append(
        Result("PB-5 validate at boundaries", MANUAL, "confirm pydantic at config/tool JSON")
    )

    # --- Session log & observability ---
    results.append(
        Result(
            "SL-1 model-visible means logged",
            PASS if _has(r"derive_messages") and _has(r"SL1Violation") else FAIL,
            "derive_messages + SL1Violation present",
        )
    )
    results.append(
        Result(
            "SL-2 structured traces",
            PASS if _has(r"SpanTimer") and _has(r"trace_id") else MANUAL,
            "turn/llm/tool spans recorded via a Tracer port",
        )
    )

    # --- Web-visible & observability ---
    spec_md = (spec / "spec.md").read_text() if (spec / "spec.md").exists() else ""
    web_visible = "## Web Acceptance" in spec_md
    results.append(
        Result(
            "WV web-visible acceptance",
            PASS if (not web_visible or "## Observability" in spec_md) else FAIL,
            "spec has Web Acceptance + Observability sections",
        )
    )
    results.append(
        Result(
            "WV-6 UI states specified",
            PASS
            if ("## Web Acceptance" not in spec_md or "## UI Requirements" in spec_md)
            else FAIL,
            "spec has ## UI Requirements (or has no web surface)",
        )
    )
    results.append(
        Result(
            "OB observability",
            PASS if _has(r"SpanTimer") and _has(r"JsonlTracer") else MANUAL,
            "spans + metrics emitted and readable via /traces (viewer in the web app)",
        )
    )

    # --- Real-world fitness & evidence (RW / SC / EV, v1.3.0) ---
    requires_coverage = _requires_coverage(spec_md)
    has_coverage = "## Real-World Coverage" in spec_md
    results.append(
        Result(
            "RW real-world coverage",
            PASS if has_coverage or not requires_coverage else FAIL,
            "spec has ## Real-World Coverage (or the feature does not touch "
            "inputs/data/model/retrieval)",
        )
    )
    if has_coverage:
        coverage_gaps = _coverage_gaps(spec_md)
        results.append(
            Result(
                "RW-3 edge & failure enumeration",
                PASS if not coverage_gaps else FAIL,
                "all six coverage bullets present with content"
                if not coverage_gaps
                else f"missing/short: {', '.join(coverage_gaps)}",
            )
        )
    # Best-practice sections for agent/LLM features (conditional).
    results.append(
        Result(
            "EV evaluation plan",
            PASS if (not requires_coverage or "## Evaluation Plan" in spec_md) else FAIL,
            "spec has ## Evaluation Plan (or the feature does not touch the model/data)",
        )
    )
    if _requires_hitl(spec_md):
        results.append(
            Result(
                "HITL specified",
                PASS if "## Human-in-the-Loop" in spec_md else FAIL,
                "spec has ## Human-in-the-Loop (it proposes a state change)",
            )
        )
    if _requires_provenance(spec_md):
        results.append(
            Result(
                "Data provenance",
                PASS if "## Data Provenance" in spec_md else FAIL,
                "spec has ## Data Provenance & Licensing (it uses external data)",
            )
        )
    results.append(
        Result(
            "EV change evidence",
            PASS
            if "## Measured Results" in spec_md or (ROOT / "specs" / "RESULTS.md").exists()
            else MANUAL,
            "specs/RESULTS.md records measured before/after evidence",
        )
    )

    # --- Deployment ---
    dockerfile = (ROOT / "Dockerfile").read_text() if (ROOT / "Dockerfile").exists() else ""
    compose = (ROOT / "docker-compose.yml").exists()
    results.append(
        Result(
            "DP deployment",
            PASS if "HEALTHCHECK" in dockerfile and compose else FAIL,
            "Dockerfile healthcheck + compose present",
        )
    )

    # --- Harness ---
    results.append(
        Result("HR-3 guides and sensors", MANUAL, "prompt/skills/contracts + tests/typecheck/evals")
    )
    results.append(
        Result(
            "HR-12 budgets",
            PASS if _has(r"CostMeter") and _has(r"BudgetSettings") else FAIL,
            "cost meter + budget settings present",
        )
    )

    # --- Decision records ---
    notes = subprocess.run(
        [sys.executable, "scripts/verify_notes.py"], cwd=ROOT, capture_output=True, text=True
    )
    results.append(
        Result(
            "DR decision records",
            PASS if notes.returncode == 0 else FAIL,
            notes.stdout.strip().splitlines()[-1] if notes.stdout.strip() else "verify_notes",
        )
    )

    # --- Testing & types ---
    unit = list((ROOT / "tests/unit").glob("test_*.py")) if (ROOT / "tests/unit").exists() else []
    pyproject = (ROOT / "pyproject.toml").read_text() if (ROOT / "pyproject.toml").exists() else ""
    results.append(
        Result(
            "TT testing & types",
            PASS if unit and "[tool.pyright]" in pyproject else FAIL,
            f"{len(unit)} unit test file(s); pyright configured",
        )
    )

    # --- Resilience & data ---
    settings_yaml = (
        (ROOT / "config/settings.yaml").read_text()
        if (ROOT / "config/settings.yaml").exists()
        else ""
    )
    results.append(
        Result(
            "RD resilience & data",
            PASS if "use_llm" in settings_yaml else MANUAL,
            "explicit use_llm switches present",
        )
    )
    results.append(Result("GH github workflow", MANUAL, "branch + PR + required checks"))

    return results


def render(spec: Path, results: list[Result]) -> str:
    lines = [
        f"# Self-review: {spec.name}",
        "",
        "Generated by `scripts/spec_review.py` (constitution SR-1..SR-3).",
        "",
        "| Clause | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for r in results:
        lines.append(f"| {r.clause} | {r.status} | {r.evidence} |")
    failed = [r for r in results if r.status == FAIL]
    lines += [
        "",
        f"**Result**: {'FAIL' if failed else 'PASS'} "
        f"({sum(1 for r in results if r.status == PASS)} auto, "
        f"{sum(1 for r in results if r.status == MANUAL)} manual, "
        f"{len(failed)} failed)",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    feature = sys.argv[1] if len(sys.argv) > 1 else None
    spec = SPECS / feature if feature else (_branch_spec() or _latest_spec())
    if spec is None or not spec.exists():
        print("No spec directory found. Pass a feature id, e.g.:")
        print("  python scripts/spec_review.py 001-agent-core")
        return 1

    results = check(spec)
    report = render(spec, results)
    (spec / "review.md").write_text(report)
    print(report)

    failed = [r for r in results if r.status == FAIL]
    if failed:
        print(f"BLOCKED: {len(failed)} clause(s) failed. Fix before opening a PR (SR-3).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
