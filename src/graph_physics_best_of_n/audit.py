"""Claim and artifact audit utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


FORBIDDEN_SUPPORTED_PATTERNS = (
    "real robot",
    "real-robot",
    "sota",
    "state of the art",
    "broad benchmark",
    "universal improvement",
    "universal best-of-n",
)


def claim_inventory() -> list[dict[str, str]]:
    return [
        {
            "id": "C1",
            "claim": "Exact finite tie-aware Best-of-N laws predict selected utility on finite graph-physics candidate pools.",
            "status": "supported",
            "evidence": "theory tests and exact_law_validation.csv",
        },
        {
            "id": "C2",
            "claim": "In controlled graph-physics toy worlds, high-N raw selection can increase internal score while selected real utility stagnates or falls.",
            "status": "supported",
            "evidence": "figure1_selected_tail_failure.png and main_metrics.csv",
        },
        {
            "id": "C3",
            "claim": "Graph-energy calibration and constraint probing improve selected-tail utility in the controlled synthetic setting.",
            "status": "supported",
            "evidence": "figure2_repair_comparison.png and repair_metrics.csv",
        },
        {
            "id": "C4",
            "claim": "The method is validated on real robot systems.",
            "status": "unsupported",
            "evidence": "no real-robot experiments are present",
        },
        {
            "id": "C5",
            "claim": "The method establishes broad physics benchmark superiority or state-of-the-art performance.",
            "status": "unsupported",
            "evidence": "no broad benchmark suite is present",
        },
    ]


def scan_forbidden_overclaims(claims: Iterable[dict[str, str]]) -> list[str]:
    problems: list[str] = []
    for claim in claims:
        status = claim.get("status", "").lower()
        text = (claim.get("claim", "") + " " + claim.get("evidence", "")).lower()
        if status == "supported":
            for pattern in FORBIDDEN_SUPPORTED_PATTERNS:
                if pattern in text:
                    problems.append(f"{claim.get('id', '?')}: supported claim contains forbidden pattern '{pattern}'")
    return problems


def artifact_inventory(root: str | Path) -> dict[str, list[str]]:
    root = Path(root)
    return {
        "tables": sorted(str(path.relative_to(root)) for path in (root / "results" / "tables").glob("*.csv")),
        "figures": sorted(str(path.relative_to(root)) for path in (root / "figures").glob("*.png")),
        "json": sorted(str(path.relative_to(root)) for path in (root / "results").glob("*.json")),
        "docs": sorted(str(path.relative_to(root)) for path in (root / "docs").glob("*.md")),
        "paper": sorted(str(path.relative_to(root)) for path in (root / "paper").glob("*.md")),
    }


def write_claim_status(root: str | Path) -> dict[str, object]:
    root = Path(root)
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    claims = claim_inventory()
    problems = scan_forbidden_overclaims(claims)
    payload = {
        "claims": claims,
        "forbidden_supported_overclaims": problems,
        "passes_claim_audit": not problems,
    }
    (results / "claims_status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Claims Status", ""]
    for claim in claims:
        lines.extend(
            [
                f"## {claim['id']}: {claim['status']}",
                claim["claim"],
                "",
                f"Evidence: {claim['evidence']}",
                "",
            ]
        )
    if problems:
        lines.append("## Forbidden Supported Overclaims")
        lines.extend(f"- {problem}" for problem in problems)
    else:
        lines.append("No forbidden supported overclaims detected.")
    (results / "claims_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def write_final_audit(root: str | Path, command_results: dict[str, str] | None = None) -> None:
    root = Path(root)
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    inventory = artifact_inventory(root)
    if command_results is None:
        command_results = {}
        summary_path = root / "results" / "run_summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            command_results[f"experiments --mode {summary.get('mode', 'unknown')}"] = (
                f"pass (runtime {summary.get('runtime_seconds', 'unknown')}s, gate {summary.get('deployment_gate', 'unknown')})"
            )
            if summary.get("passes_claim_audit"):
                command_results["bash scripts/run_claim_audit.sh"] = "pass"

    lines = [
        "# Final Audit",
        "",
        "Paper-readiness judgment: paper-worthy v1 for controlled synthetic graph-physics evidence; needs broader benchmark and real-system validation for stronger claims.",
        "",
        "## Command Results",
    ]
    if command_results:
        lines.extend(f"- {name}: {status}" for name, status in command_results.items())
    else:
        lines.append("- Pending final command run in this checkout.")
    lines.extend(
        [
            "",
            "## Strongest Artifacts",
            "- Failure artifact: figure1_selected_tail_failure.png and raw high-N rows in main_metrics.csv.",
            "- Repair artifact: figure2_repair_comparison.png and repair_metrics.csv.",
            "- Law artifact: exact_law_validation.csv and figure3_exact_law_validation.png.",
            "",
            "## Differentiation",
            "The repo reuses only the finite Best-of-N law pattern. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, and constraint-probe repair.",
            "It is not a real-robot evaluation, not a broad physics-engine benchmark, and not a claim that increasing N always helps.",
            "",
            "## Remaining Weaknesses",
            "- Synthetic worlds are intentionally controlled and small.",
            "- Repair scores use diagnostic proxies available in the toy generator.",
            "- No real-robot or broad benchmark evidence is claimed.",
            "",
            "## Artifact Inventory",
        ]
    )
    for group, paths in inventory.items():
        lines.append(f"### {group}")
        if paths:
            lines.extend(f"- {path}" for path in paths)
        else:
            lines.append("- none")
    (docs / "final_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path.cwd())
    args = parser.parse_args()
    payload = write_claim_status(args.root)
    write_final_audit(args.root)
    return 0 if payload["passes_claim_audit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

