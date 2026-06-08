from pathlib import Path

from graph_physics_best_of_n.audit import claim_inventory, scan_forbidden_overclaims, write_claim_status


def test_supported_claims_have_no_forbidden_overclaims(tmp_path: Path):
    claims = claim_inventory()
    assert scan_forbidden_overclaims(claims) == []
    payload = write_claim_status(tmp_path)
    assert payload["passes_claim_audit"] is True
    assert (tmp_path / "results" / "claims_status.json").exists()

