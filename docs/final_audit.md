# Final Audit

Paper-readiness judgment: paper-worthy v1 for controlled synthetic graph-physics evidence; needs broader benchmark and real-system validation for stronger claims.

## Command Results
- gh --version: pass (GitHub CLI 2.92.0, 2026-04-28)
- gh auth status: failed (not logged into any GitHub hosts)
- git ls-remote origin: pass (remote exists and returned no refs; treated as empty history)
- bash scripts/run_smoke.sh: pass (runtime 34.523s, gate allow_high_n_with_combined_repair)
- bash scripts/run_all.sh: pass (runtime 249.818s, gate allow_high_n_with_combined_repair)
- bash scripts/run_claim_audit.sh: pass
- pytest: pass (5 tests passed in 16.24s)

## Publication
- Local repository: initialized on branch main.
- Origin: https://github.com/Jason-Wang313/best-of-n-graph-world-model.git.
- Push result: pending at pre-commit audit time.

## Strongest Artifacts
- Failure artifact: figure1_selected_tail_failure.png and raw high-N rows in main_metrics.csv.
- Repair artifact: figure2_repair_comparison.png and repair_metrics.csv.
- Law artifact: exact_law_validation.csv and figure3_exact_law_validation.png.

## Differentiation
The repo reuses only the finite Best-of-N law pattern. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, and constraint-probe repair.
It is not a real-robot evaluation, not a broad physics-engine benchmark, and not a claim that increasing N always helps.

## Remaining Weaknesses
- Synthetic worlds are intentionally controlled and small.
- Repair scores use diagnostic proxies available in the toy generator.
- No real-robot or broad benchmark evidence is claimed.

## Artifact Inventory
### tables
- results\tables\exact_law_validation.csv
- results\tables\main_metrics.csv
- results\tables\repair_metrics.csv
- results\tables\seed_metrics.csv
### figures
- figures\figure1_selected_tail_failure.png
- figures\figure2_repair_comparison.png
- figures\figure3_exact_law_validation.png
### json
- results\claims_status.json
- results\run_summary.json
### docs
- docs\claims.md
- docs\final_audit.md
### paper
- paper\abstract.md
