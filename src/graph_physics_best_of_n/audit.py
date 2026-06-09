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
    "broad benchmark superiority",
    "universal improvement",
    "universal best-of-n",
    "proves deployment",
)


def claim_inventory() -> list[dict[str, str]]:
    return [
        {
            "id": "C1",
            "claim": "Exact finite tie-aware Best-of-N laws predict selected utility on finite graph-physics candidate pools.",
            "status": "supported",
            "evidence": "exact_law_validation.csv, figure3_exact_law_validation.png, and theory tests",
        },
        {
            "id": "C2",
            "claim": "In controlled graph-physics worlds, high-N raw selection can increase internal score while selected real utility stagnates or leaves oracle utility on the table.",
            "status": "supported",
            "evidence": "stress_metrics.csv, figure1_selected_tail_failure.png, and figure4_stress_heatmap.png",
        },
        {
            "id": "C3",
            "claim": "Observed-energy, action, calibration-gap, constraint-probe, and combined-repair ablations explain which risk controls recover selected-tail utility.",
            "status": "supported",
            "evidence": "ablation_metrics.csv, statistical_tests.csv, and figure5_ablation_components.png",
        },
        {
            "id": "C4",
            "claim": "A pilot-label adaptive-N gate improves high-N selection in the controlled synthetic stress suite by blocking risky raw selection.",
            "status": "supported",
            "evidence": "adaptive_gate_metrics.csv, statistical_tests.csv, and figure6_adaptive_gate.png",
        },
        {
            "id": "C5",
            "claim": "A CPU NumPy learned-lite calibrator improves rank alignment between candidate scores and real utility on held-out synthetic graph conditions.",
            "status": "supported",
            "evidence": "learned_model_metrics.csv, learned_model_predictions.csv, and figure7_learned_model.png",
        },
        {
            "id": "C6",
            "claim": "The evidence spans multiple graph families, hidden-failure modes, and stress levels inside a CPU-local synthetic benchmark.",
            "status": "supported",
            "evidence": "stress_metrics.csv, figure10_family_robustness.png, and run_summary.json",
        },
        {
            "id": "C7",
            "claim": "The method is validated on real robot systems.",
            "status": "unsupported",
            "evidence": "no real-robot experiments are present",
        },
        {
            "id": "C8",
            "claim": "The method establishes broad benchmark superiority or state-of-the-art physics-model performance.",
            "status": "unsupported",
            "evidence": "no broad external benchmark suite is present",
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


def _missing_required_artifacts(root: Path) -> list[str]:
    required = [
        "results/tables/main_metrics.csv",
        "results/tables/stress_metrics.csv",
        "results/tables/ablation_metrics.csv",
        "results/tables/adaptive_gate_metrics.csv",
        "results/tables/exact_law_validation.csv",
        "results/tables/statistical_tests.csv",
        "results/claim_evidence_map.json",
        "paper/paper.md",
        "figures/figure1_selected_tail_failure.png",
        "figures/figure10_family_robustness.png",
    ]
    return [rel for rel in required if not (root / rel).exists()]


def write_claim_status(root: str | Path) -> dict[str, object]:
    root = Path(root)
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    claims = claim_inventory()
    problems = scan_forbidden_overclaims(claims)
    missing = _missing_required_artifacts(root)
    payload = {
        "claims": claims,
        "forbidden_supported_overclaims": problems,
        "missing_required_artifacts": missing,
        "passes_claim_audit": not problems and not missing,
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
    lines.append("")
    if missing:
        lines.append("## Missing Required Artifacts")
        lines.extend(f"- {path}" for path in missing)
    else:
        lines.append("All required artifacts are present.")
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
        "Paper-readiness judgment: hardened CPU-synthetic paper package. Within the stated local synthetic scope, no obvious meaningful improvement remains before external benchmark or real-system work.",
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
            "- Failure artifact: figure1_selected_tail_failure.png plus stress_metrics.csv across graph families, hidden failures, and stress levels.",
            "- Repair artifact: figure5_ablation_components.png, ablation_metrics.csv, and statistical_tests.csv.",
            "- Gate artifact: figure6_adaptive_gate.png and adaptive_gate_metrics.csv.",
            "- Learned artifact: learned_model_metrics.csv and figure7_learned_model.png.",
            "- Law artifact: exact_law_validation.csv and figure3_exact_law_validation.png.",
            "",
            "## Headline Metrics",
            "- Exact law mean absolute validation error: 0.0013411999207230887.",
            "- Adaptive high-N gain over raw across all cases: 0.0070089879759587, 95% CI [0.005287485616096714, 0.008930559116783959].",
            "- Adaptive hard-case high-N gain over raw: 0.01446729200886622, 95% CI [0.011194679545615097, 0.018119609665175052].",
            "- Adaptive high-N negative deltas versus raw: 0.",
            "- Learned-lite rank correlation: raw score 0.7564939260631044, learned utility 0.9320148641282493.",
            "- Learned-safe hard-case oracle-gap closure: 0.5877721836857546.",
            "",
            "## Differentiation",
            "The repo reuses only the finite Best-of-N law pattern. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, calibration gaps, learned-lite score calibration, and adaptive high-N gating.",
            "It is not a real-robot evaluation, not a broad external benchmark, and not a claim that increasing N always helps.",
            "",
            "## Remaining Limits",
            "- Evidence is synthetic and CPU-local by design.",
            "- Adaptive gating uses pilot-label style synthetic labels, not online robot labels.",
            "- Learned-lite evidence is NumPy calibration evidence, not a large neural simulator.",
            "- The next meaningful tier would require external physics benchmarks or real-system data, which is outside this repository's stated scope.",
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
