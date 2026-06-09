# Final Audit

Paper-readiness judgment: hardened CPU-synthetic paper package. Within the stated local synthetic scope, no obvious meaningful improvement remains before external benchmark or real-system work.

## Command Results
- experiments --mode bulletproof: pass (runtime 1343.253s, gate allow_high_n_with_adaptive_gate)
- bash scripts/run_claim_audit.sh: pass
- pytest: pass (9 tests passed in 11.21s)

## Publication
- Local branch: main.
- Origin: https://github.com/Jason-Wang313/best-of-n-graph-world-model.git.
- Submission package commit: pending commit and push for this manuscript pass.
- Push result: pending.

## Strongest Artifacts
- Failure artifact: figure1_selected_tail_failure.png plus stress_metrics.csv across graph families, hidden failures, and stress levels.
- Repair artifact: figure5_ablation_components.png, ablation_metrics.csv, and statistical_tests.csv.
- Gate artifact: figure6_adaptive_gate.png and adaptive_gate_metrics.csv.
- Learned artifact: learned_model_metrics.csv and figure7_learned_model.png.
- Law artifact: exact_law_validation.csv and figure3_exact_law_validation.png.

## Headline Metrics
- Exact law mean absolute validation error: 0.0013411999207230887.
- Adaptive high-N gain over raw across all cases: 0.0070089879759587, 95% CI [0.005287485616096714, 0.008930559116783959].
- Adaptive hard-case high-N gain over raw: 0.01446729200886622, 95% CI [0.011194679545615097, 0.018119609665175052].
- Adaptive high-N negative deltas versus raw: 0.
- Learned-lite rank correlation: raw score 0.7564939260631044, learned utility 0.9320148641282493.
- Learned-safe hard-case oracle-gap closure: 0.5877721836857546.

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
