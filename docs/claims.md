# Claims

This file is the reviewer-facing claim boundary for the repository. Supported
claims must point to concrete artifacts. Unsupported claims are explicitly
listed so the paper package does not imply evidence that is not present.

## Supported

### C1: Exact finite score-tie law

Exact finite score-tie laws predict selected utility for finite graph-physics
candidate pools.

Evidence:

- `src/graph_constraint_tail_audit/theory.py`
- `tests/test_theory.py`
- `results/tables/exact_law_validation.csv`
- `figures/figure3_exact_law_validation.png`

### C2: Selected-tail failure

Controlled graph-physics high-`N` selection can expose selected-tail failures:
internal score improves while real utility remains below the oracle tail.

Evidence:

- `results/tables/stress_metrics.csv`
- `results/tables/main_metrics.csv`
- `figures/figure1_selected_tail_failure.png`
- `figures/figure4_stress_heatmap.png`
- `figures/figure9_hidden_energy_by_n.png`

### C3: Repair and ablation evidence

Observed-energy penalties, action penalties, calibration-gap penalties,
constraint probes, graph-energy calibration, and combined repair have measurable
roles in selected-tail recovery inside the synthetic suite.

Evidence:

- `src/graph_constraint_tail_audit/selection.py`
- `results/tables/ablation_metrics.csv`
- `results/tables/repair_metrics.csv`
- `results/tables/statistical_tests.csv`
- `figures/figure5_ablation_components.png`
- `figures/figure8_oracle_gap_closure.png`

### C4: Pilot-label adaptive gate

A pilot-label adaptive gate improves high-`N` selection in the controlled
synthetic stress suite by blocking risky raw selections.

Evidence:

- `results/tables/adaptive_gate_metrics.csv`
- `results/tables/statistical_tests.csv`
- `figures/figure6_adaptive_gate.png`

Caveat: this is pilot-label synthetic evidence, not an online deployment
guarantee.

### C5: Learned-lite calibration

A CPU NumPy learned-lite calibrator improves held-out rank alignment between
candidate scores and real utility on synthetic graph conditions.

Evidence:

- `src/graph_constraint_tail_audit/learned_model.py`
- `results/tables/learned_model_metrics.csv`
- `results/tables/learned_model_predictions.csv`
- `figures/figure7_learned_model.png`

Caveat: this is lightweight synthetic calibration evidence, not a claim about a
large learned simulator.

### C6: Synthetic coverage

The stress suite covers multiple graph families, hidden-failure modes, and
stress levels inside a CPU-local synthetic benchmark.

Evidence:

- `src/graph_constraint_tail_audit/graph_physics.py`
- `results/tables/stress_metrics.csv`
- `figures/figure10_family_robustness.png`
- `results/run_summary.json`

### C7: V4 graph-dynamics probe bridge

The v4 audit adds recognized graph-dynamics protocol probes for spring
interaction networks, latent-edge inference, long-horizon graph simulation,
chain rest-length shift, and random-geometric damping.

Evidence:

- `results/v4_frozen_evidence/v4_benchmark_protocol_bridge.csv`
- `results/v4_frozen_evidence/v4_cell_gate_matrix.csv`
- `results/v4_frozen_evidence/v4_claim_gates.csv`
- `results/figures/v4/v4_benchmark_protocol_bridge.pdf`

Caveat: these are standardized graph-dynamics probes inside this artifact, not
external held-out datasets or reproduced SOTA baselines.

## Unsupported

### C8: Real-system validation

The method is validated on real robot systems.

Evidence status: unsupported. No real-robot experiments are present.

### C9: Broad external benchmark superiority

The method establishes broad benchmark superiority or state-of-the-art
physics-model performance.

Evidence status: unsupported. V4 adds recognized graph-dynamics probes, but no
external held-out dataset or reproduced SOTA baseline is present.

### C10: Universal high-`N` improvement

Increasing `N` universally improves selected real utility.

Evidence status: unsupported. The repository studies selected-tail risk and
repairs in controlled graph worlds, not a universal monotonic-improvement
claim.

### C11: Deployment safety

The adaptive gate proves deployment safety beyond the controlled synthetic
setting.

Evidence status: unsupported. The adaptive gate is explicitly pilot-label and
synthetic.
