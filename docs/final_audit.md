# Final Audit

Paper-readiness judgment: hardened CPU-synthetic paper package. Within the stated local synthetic scope, no obvious meaningful improvement remains before external benchmark or real-system work.

## Command Results
- gh --version: pass (GitHub CLI 2.92.0, 2026-04-28)
- gh auth status: failed (not logged into any GitHub hosts; git credential push path will be used)
- git ls-remote origin refs/heads/main: pass (pre-push remote main at 3f713263d330c9b07ed660379c3363159105d968)
- bash scripts/run_smoke.sh: pass (runtime 27.508s, health-check artifact run)
- bash scripts/run_all.sh: pass (runtime 478.589s, gate allow_high_n_with_adaptive_gate)
- bash scripts/run_bulletproof.sh: pass (runtime 1729.208s, 80 conditions, 22400 seed rows, gate allow_high_n_with_adaptive_gate)
- bash scripts/run_claim_audit.sh: pass
- pytest: pass (9 tests passed in 46.96s)

## Publication
- Local branch: main.
- Origin: https://github.com/Jason-Wang313/best-of-n-graph-world-model.git.
- Pre-push local HEAD: 3f713263d330c9b07ed660379c3363159105d968.
- Push result: pending at pre-commit audit time.

## Strongest Artifacts
- Failure artifact: figure1_selected_tail_failure.png plus stress_metrics.csv across graph families, hidden failures, and stress levels.
- Repair artifact: figure5_ablation_components.png, ablation_metrics.csv, and statistical_tests.csv.
- Gate artifact: figure6_adaptive_gate.png and adaptive_gate_metrics.csv.
- Learned artifact: learned_model_metrics.csv and figure7_learned_model.png.
- Law artifact: exact_law_validation.csv and figure3_exact_law_validation.png.

## Differentiation
The repo reuses only the finite Best-of-N law pattern. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, calibration gaps, learned-lite score calibration, and adaptive high-N gating.
It is not a real-robot evaluation, not a broad external benchmark, and not a claim that increasing N always helps.

## Remaining Limits
- Evidence is synthetic and CPU-local by design.
- Adaptive gating uses pilot-label style synthetic labels, not online robot labels.
- Learned-lite evidence is NumPy calibration evidence, not a large neural simulator.
- The next meaningful tier would require external physics benchmarks or real-system data, which is outside this repository's stated scope.

## Artifact Inventory
### tables
- results\tables\ablation_metrics.csv
- results\tables\adaptive_gate_metrics.csv
- results\tables\exact_law_validation.csv
- results\tables\learned_model_metrics.csv
- results\tables\learned_model_predictions.csv
- results\tables\main_metrics.csv
- results\tables\repair_metrics.csv
- results\tables\seed_metrics.csv
- results\tables\statistical_tests.csv
- results\tables\stress_metrics.csv
### figures
- figures\figure10_family_robustness.png
- figures\figure1_selected_tail_failure.png
- figures\figure2_repair_comparison.png
- figures\figure3_exact_law_validation.png
- figures\figure4_stress_heatmap.png
- figures\figure5_ablation_components.png
- figures\figure6_adaptive_gate.png
- figures\figure7_learned_model.png
- figures\figure8_oracle_gap_closure.png
- figures\figure9_hidden_energy_by_n.png
### json
- results\claim_evidence_map.json
- results\claims_status.json
- results\run_summary.json
### docs
- docs\claims.md
- docs\final_audit.md
### paper
- paper\abstract.md
- paper\paper.md
