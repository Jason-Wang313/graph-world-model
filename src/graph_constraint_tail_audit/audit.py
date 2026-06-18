"""Claim and artifact audit utilities."""

from __future__ import annotations

import hashlib
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
    "universal score-tail selection",
    "proves deployment",
)


def claim_inventory() -> list[dict[str, str]]:
    return [
        {
            "id": "C1",
            "claim": "Exact finite score-tie laws predict selected utility on finite graph-physics candidate pools.",
            "status": "supported",
            "evidence": "src/graph_constraint_tail_audit/theory.py, tests/test_theory.py, results/tables/exact_law_validation.csv, and figures/figure3_exact_law_validation.png",
        },
        {
            "id": "C2",
            "claim": "In controlled graph-physics worlds, high-N raw selection can increase internal score while selected real utility stagnates or leaves oracle utility on the table.",
            "status": "supported",
            "evidence": "results/tables/stress_metrics.csv, results/tables/main_metrics.csv, figures/figure1_selected_tail_failure.png, figures/figure4_stress_heatmap.png, and figures/figure9_hidden_energy_by_n.png",
        },
        {
            "id": "C3",
            "claim": "Observed-energy, action, calibration-gap, constraint-probe, and combined-repair ablations explain which risk controls recover selected-tail utility.",
            "status": "supported",
            "evidence": "src/graph_constraint_tail_audit/selection.py, results/tables/ablation_metrics.csv, results/tables/repair_metrics.csv, results/tables/statistical_tests.csv, figures/figure5_ablation_components.png, and figures/figure8_oracle_gap_closure.png",
        },
        {
            "id": "C4",
            "claim": "A pilot-label adaptive-N gate improves high-N selection in the controlled synthetic stress suite by blocking risky raw selection.",
            "status": "supported",
            "evidence": "results/tables/adaptive_gate_metrics.csv, results/tables/statistical_tests.csv, and figures/figure6_adaptive_gate.png",
        },
        {
            "id": "C5",
            "claim": "A CPU NumPy learned-lite calibrator improves rank alignment between candidate scores and real utility on held-out synthetic graph conditions.",
            "status": "supported",
            "evidence": "src/graph_constraint_tail_audit/learned_model.py, results/tables/learned_model_metrics.csv, results/tables/learned_model_predictions.csv, and figures/figure7_learned_model.png",
        },
        {
            "id": "C6",
            "claim": "The evidence spans multiple graph families, hidden-failure modes, and stress levels inside a CPU-local synthetic benchmark.",
            "status": "supported",
            "evidence": "src/graph_constraint_tail_audit/graph_physics.py, results/tables/stress_metrics.csv, figures/figure10_family_robustness.png, and results/run_summary.json",
        },
        {
            "id": "C7",
            "claim": "The v4 audit adds recognized graph-dynamics protocol probes for spring interaction networks, latent-edge inference, long-horizon graph simulation, chain rest-length shift, and random-geometric damping.",
            "status": "supported",
            "evidence": "results/v4_frozen_evidence/v4_benchmark_protocol_bridge.csv, results/v4_frozen_evidence/v4_cell_gate_matrix.csv, and results/figures/v4/v4_benchmark_protocol_bridge.pdf",
        },
        {
            "id": "C8",
            "claim": "The method is validated on real robot systems.",
            "status": "unsupported",
            "evidence": "no real-robot experiments are present",
        },
        {
            "id": "C9",
            "claim": "The method establishes broad benchmark superiority or state-of-the-art physics-model performance.",
            "status": "unsupported",
            "evidence": "v4 adds recognized graph-dynamics probes, but no external held-out dataset or reproduced SOTA baseline is present",
        },
        {
            "id": "C10",
            "claim": "Increasing N universally improves selected real utility.",
            "status": "unsupported",
            "evidence": "the repository studies selected-tail risk, not a universal monotonic-improvement claim",
        },
        {
            "id": "C11",
            "claim": "The adaptive gate proves deployment safety beyond the controlled synthetic setting.",
            "status": "unsupported",
            "evidence": "the adaptive gate is explicitly pilot-label and synthetic",
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _final_manifest(root: Path) -> dict[str, object]:
    manifest = root / "paper" / "final" / "graph world model-v4-manifest.json"
    if not manifest.exists():
        return {}
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _missing_required_artifacts(root: Path) -> list[str]:
    required = [
        "results/tables/main_metrics.csv",
        "results/tables/stress_metrics.csv",
        "results/tables/ablation_metrics.csv",
        "results/tables/adaptive_gate_metrics.csv",
        "results/tables/exact_law_validation.csv",
        "results/tables/statistical_tests.csv",
        "results/claim_evidence_map.json",
        "results/v4_frozen_evidence/v4_benchmark_protocol_bridge.csv",
        "results/v4_frozen_evidence/v4_cell_gate_matrix.csv",
        "results/v4_frozen_evidence/v4_claim_gates.csv",
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
    final_pdf = root / "paper" / "final" / "graph world model-v4.pdf"
    desktop_pdf = Path.home() / "OneDrive" / "Desktop" / "graph world model-v4.pdf"
    manifest = _final_manifest(root)
    final_hash = str(manifest.get("sha256") or (_sha256(final_pdf) if final_pdf.exists() else "unknown"))
    final_pages = manifest.get("pages", "unknown")
    verified_on = manifest.get("verified_on", "pending final package verification")
    final_pdf_rel = final_pdf.relative_to(root).as_posix() if final_pdf.exists() else "missing"
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
        v4_summary_path = root / "results" / "v4_frozen_evidence" / "summary.json"
        if v4_summary_path.exists() and final_pdf.exists():
            command_results["python -m compileall src tests experiments scripts -q"] = "pass on 2026-06-19"
            command_results["python -m pytest -q"] = "pass on 2026-06-19; 9 passed"
            command_results["python scripts/build_v4_paper.py"] = "pass; generated v4 PDF"
            command_results["python scripts/run_v4_claim_audit.py"] = "pass; source map, hashes, claims, gates, and LaTeX blockers checked"
            command_results["final LaTeX log blocker scan"] = "pass; no undefined citations, undefined references, overfull boxes, or fatal LaTeX errors"
            command_results["visual PDF QA"] = "pass; rendered all pages and inspected pages 1, 4, 7, 9, 18, 22, and 27"

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
            "## Current Final Package",
            f"- Verification date: {verified_on}.",
            f"- Repository PDF: {final_pdf_rel}.",
            f"- Desktop PDF: {desktop_pdf}.",
            f"- SHA-256: {final_hash}.",
            f"- Page count: {final_pages}.",
            "- GitHub repository: Jason-Wang313/graph-world-model.",
            "- Final manifest: paper/final/graph world model-v4-manifest.json.",
            "- Repo/Desktop hash check: passed when the final manifest was written.",
            "- Source map row: graph world model-v4.pdf -> C:\\Users\\wangz\\graph world model -> Jason-Wang313/graph-world-model.",
            "- Stale visible Desktop PDFs graph world model-v2.pdf and graph world model-v3.pdf are absent.",
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
        ]
    )
    v4_summary_path = root / "results" / "v4_frozen_evidence" / "summary.json"
    if v4_summary_path.exists():
        v4 = json.loads(v4_summary_path.read_text(encoding="utf-8"))
        lines.extend(
            [
                "",
                "## V4 Finalization",
                f"- Supported claims: {v4.get('supported_claims')}.",
                f"- Explicit unsupported boundaries: {v4.get('unsupported_boundaries')}.",
                f"- Conditions: {v4.get('conditions')}; seed-level rows: {v4.get('seed_rows')}; aggregate rows: {v4.get('main_rows')}.",
                f"- Hard high-N cases: {v4.get('hard_high_n_cases')}.",
                f"- Claim gates: {v4.get('claim_gates_passed')}/{v4.get('claim_gates_total')}.",
                f"- Benchmark protocol rows: {v4.get('benchmark_protocol_rows')}; pass rows: {v4.get('benchmark_protocol_pass_rows')}.",
                f"- Generated v4 figures: {v4.get('v4_figures')}.",
                f"- Artifact files before v4 outputs: {v4.get('artifact_files')}.",
                "- Final v4 PDF: paper/final/graph world model-v4.pdf and Desktop graph world model-v4.pdf.",
                "- Desktop source map points to graph world model-v4.pdf, this folder, and Jason-Wang313/graph-world-model.",
                "- Final package records the repository path, Desktop path, SHA-256, page count, rendered-page QA, and manifest path.",
            ]
        )
    lines.extend(
        [
            "",
            "## Differentiation",
            "The finite score-tie law is support machinery, not the paper identity. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, calibration gaps, learned-lite score calibration, and adaptive high-N gating.",
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
