# Claims Status

## C1: supported
Exact finite tie-aware Best-of-N laws predict selected utility on finite graph-physics candidate pools.

Evidence: src/graph_physics_best_of_n/theory.py, tests/test_theory.py, results/tables/exact_law_validation.csv, and figures/figure3_exact_law_validation.png

## C2: supported
In controlled graph-physics worlds, high-N raw selection can increase internal score while selected real utility stagnates or leaves oracle utility on the table.

Evidence: results/tables/stress_metrics.csv, results/tables/main_metrics.csv, figures/figure1_selected_tail_failure.png, figures/figure4_stress_heatmap.png, and figures/figure9_hidden_energy_by_n.png

## C3: supported
Observed-energy, action, calibration-gap, constraint-probe, and combined-repair ablations explain which risk controls recover selected-tail utility.

Evidence: src/graph_physics_best_of_n/selection.py, results/tables/ablation_metrics.csv, results/tables/repair_metrics.csv, results/tables/statistical_tests.csv, figures/figure5_ablation_components.png, and figures/figure8_oracle_gap_closure.png

## C4: supported
A pilot-label adaptive-N gate improves high-N selection in the controlled synthetic stress suite by blocking risky raw selection.

Evidence: results/tables/adaptive_gate_metrics.csv, results/tables/statistical_tests.csv, and figures/figure6_adaptive_gate.png

## C5: supported
A CPU NumPy learned-lite calibrator improves rank alignment between candidate scores and real utility on held-out synthetic graph conditions.

Evidence: src/graph_physics_best_of_n/learned_model.py, results/tables/learned_model_metrics.csv, results/tables/learned_model_predictions.csv, and figures/figure7_learned_model.png

## C6: supported
The evidence spans multiple graph families, hidden-failure modes, and stress levels inside a CPU-local synthetic benchmark.

Evidence: src/graph_physics_best_of_n/graph_physics.py, results/tables/stress_metrics.csv, figures/figure10_family_robustness.png, and results/run_summary.json

## C7: unsupported
The method is validated on real robot systems.

Evidence: no real-robot experiments are present

## C8: unsupported
The method establishes broad benchmark superiority or state-of-the-art physics-model performance.

Evidence: no broad external benchmark suite is present

## C9: unsupported
Increasing N universally improves selected real utility.

Evidence: the repository studies selected-tail risk, not a universal monotonic-improvement claim

## C10: unsupported
The adaptive gate proves deployment safety beyond the controlled synthetic setting.

Evidence: the adaptive gate is explicitly pilot-label and synthetic

No forbidden supported overclaims detected.

All required artifacts are present.
