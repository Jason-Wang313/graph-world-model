from pathlib import Path

from graph_constraint_tail_audit.audit import claim_inventory, scan_forbidden_overclaims, write_claim_status


REQUIRED = [
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


def _touch_required(root: Path) -> None:
    for rel in REQUIRED:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")


def test_supported_claims_have_no_forbidden_overclaims(tmp_path: Path):
    claims = claim_inventory()
    assert scan_forbidden_overclaims(claims) == []
    _touch_required(tmp_path)
    payload = write_claim_status(tmp_path)
    assert payload["passes_claim_audit"] is True
    assert (tmp_path / "results" / "claims_status.json").exists()


def test_claim_audit_fails_when_required_artifacts_are_missing(tmp_path: Path):
    payload = write_claim_status(tmp_path)
    assert payload["passes_claim_audit"] is False
    assert payload["missing_required_artifacts"]
