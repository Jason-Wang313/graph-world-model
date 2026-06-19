# Final Audit

Paper-readiness judgment: hardened CPU-synthetic paper package. Within the stated local synthetic scope, no obvious meaningful improvement remains before external benchmark or real-system work.

## Command Results
- experiments --mode bulletproof: pass (runtime 1343.253s, gate allow_high_n_with_adaptive_gate)
- bash scripts/run_claim_audit.sh: pass
- python -m compileall src tests experiments scripts -q: pass on 2026-06-19
- python -m pytest -q: pass on 2026-06-19; 9 passed
- python scripts/build_v4_paper.py: pass; generated v4 PDF
- python scripts/run_v4_claim_audit.py: pass; source map, hashes, claims, gates, and LaTeX blockers checked
- final LaTeX log blocker scan: pass; no undefined citations, undefined references, overfull boxes, or fatal LaTeX errors
- boxed-link rebuild from frozen artifacts: pass; repository and Desktop PDFs match
- PDF annotation link audit: pass; 74 annotations with 31 green citation boxes, 19 red internal-reference boxes, and 24 cyan URL/file boxes, all using 1pt visible borders
- visual PDF QA: pass; rendered selected high-risk pages 1, 2, 3, 5, 9, 10, 11, 15, 20, 21, 25, and 27 at moderate DPI

## Current Final Package
- Verification date: 2026-06-19.
- Repository PDF: paper/final/graph world model-v4.pdf.
- Desktop PDF: C:\Users\wangz\OneDrive\Desktop\graph world model-v4.pdf.
- SHA-256: 89DDDB261E01ACAA8705B9AF117F496584500D7C398DE5C95F623780DB6B5EF4.
- Page count: 27.
- GitHub repository: Jason-Wang313/graph-world-model.
- Final manifest: paper/final/graph world model-v4-manifest.json.
- Repo/Desktop hash check: passed when the final manifest was written.
- Source map row: graph world model-v4.pdf -> C:\Users\wangz\graph world model -> Jason-Wang313/graph-world-model.
- Stale visible Desktop PDFs graph world model-v2.pdf and graph world model-v3.pdf are absent.

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

## V4 Finalization
- Supported claims: 7.
- Explicit unsupported boundaries: 4.
- Conditions: 80; seed-level rows: 22400; aggregate rows: 5600.
- Hard high-N cases: 155.
- Claim gates: 10/10.
- Benchmark protocol rows: 5; pass rows: 5.
- Generated v4 figures: 9.
- Artifact files before v4 outputs: 60.
- Final v4 PDF: paper/final/graph world model-v4.pdf and Desktop graph world model-v4.pdf.
- Desktop source map points to graph world model-v4.pdf, this folder, and Jason-Wang313/graph-world-model.
- Final package records the repository path, Desktop path, SHA-256, page count, rendered-page QA, and manifest path.

## Differentiation
The finite score-tie law is support machinery, not the paper identity. The scientific object is graph-structured toy physics: observed springs, hidden constraints, graph-energy checks, calibration gaps, learned-lite score calibration, and adaptive high-N gating.
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
