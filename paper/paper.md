# Constraint Shadows in Graph World Models

## Abstract

Graph-structured world models often score imagined futures using only the
constraints encoded in the learned or specified graph. We study a controlled
constraint-shadow failure mode: as the number of sampled
futures grows, the selected future can move into a high-score tail that
exploits missing or miscalibrated graph constraints, improving internal score
while leaving executed utility below the oracle tail. We give a finite
finite score-tie law for top-score candidate pools, validate it empirically,
and test graph-energy, action, calibration-gap, constraint-probe,
combined-repair, adaptive-gating, and learned-lite calibration controls in a
CPU-only synthetic mass-spring stress suite. The evidence is intentionally
scoped to synthetic graph physics. It is not real-robot evidence, not an
external physics-engine benchmark, and not a broad performance claim.

## Submission Scope

This manuscript package makes one narrow claim: in controlled CPU-local
graph-physics candidate pools, high-`N` selection can expose a mismatch between
internal graph score and real utility, and simple risk controls can reduce that
mismatch in the same synthetic suite.

Evidence: `results/tables/stress_metrics.csv`,
`results/tables/statistical_tests.csv`, `figures/figure1_selected_tail_failure.png`,
`figures/figure4_stress_heatmap.png`, and `results/claim_evidence_map.json`.

This package does not claim real-system validation, external benchmark
superiority, state-of-the-art performance, or a universal rule that increasing
`N` improves deployed behavior. Unsupported claims are listed explicitly in
the claim audit rather than left implicit.

Evidence: `docs/claims.md`, `results/claims_status.md`, and
`docs/final_audit.md`.

## Contributions

1. Finite-pool law. We state and validate an exact score-tie law for selected
   utility under top-score selection from a finite scored pool.

   Evidence: `src/graph_constraint_tail_audit/theory.py`,
   `tests/test_theory.py`, `results/tables/exact_law_validation.csv`, and
   `figures/figure3_exact_law_validation.png`.

2. Synthetic graph-physics stress suite. We instantiate the law in controlled
   mass-spring graph worlds with five graph families, five hidden-failure
   modes, and three stress levels.

   Evidence: `src/graph_constraint_tail_audit/graph_physics.py`,
   `results/tables/stress_metrics.csv`, `results/run_summary.json`, and
   `figures/figure10_family_robustness.png`.

3. Selector and repair audit. We compare raw selection with observed-energy,
   action, calibration-gap, graph-energy, constraint-probe, combined-repair,
   adaptive-gate, random, and oracle selectors.

   Evidence: `src/graph_constraint_tail_audit/selection.py`,
   `results/tables/ablation_metrics.csv`,
   `results/tables/repair_metrics.csv`,
   `results/tables/statistical_tests.csv`, `figures/figure5_ablation_components.png`,
   and `figures/figure8_oracle_gap_closure.png`.

4. Pilot-label adaptive gating. We evaluate a deliberately scoped adaptive
   gate that blocks risky raw high-`N` selections in the synthetic suite.

   Evidence: `results/tables/adaptive_gate_metrics.csv`,
   `results/tables/statistical_tests.csv`, and
   `figures/figure6_adaptive_gate.png`.

5. Learned-lite calibration. We test whether a CPU NumPy ridge calibrator can
   improve held-out rank alignment between candidate features and real utility
   in synthetic graph conditions.

   Evidence: `src/graph_constraint_tail_audit/learned_model.py`,
   `results/tables/learned_model_metrics.csv`,
   `results/tables/learned_model_predictions.csv`, and
   `figures/figure7_learned_model.png`.

## Introduction

Top-score graph-world selection is attractive because it is operationally simple. A model
samples `N` candidate futures, scores them, and executes the highest-scoring
candidate. If the score is aligned with real utility, larger `N` can expose
better options. If the score is miscalibrated in the tail, larger `N` can
instead select candidates that are excellent under the model's internal
constraints and poor under the real evaluator.

Graph-structured physics is a useful controlled setting for this question.
The model's imagined graph can omit edges, use shifted rest lengths, alias a
topology, understate damping, or drift over longer horizons. These are not
claims about any particular deployed robot or external simulator. They are
small, inspectable failure modes where the gap between "score under the graph
the model sees" and "utility under the graph that is actually evaluated" is
easy to audit.

The central empirical pattern is selected-tail failure. Raw high-`N` selection
can improve selected internal score while selected real utility leaves oracle
utility on the table. Repairs and gates do not make this a solved deployment
problem. They show, within this benchmark, that graph-energy checks,
calibration-gap checks, hidden-risk probes, and pilot-label gating reduce the
tail mismatch measured by the suite.

Evidence: `figures/figure1_selected_tail_failure.png`,
`figures/figure9_hidden_energy_by_n.png`,
`results/tables/main_metrics.csv`, and `results/tables/stress_metrics.csv`.

## Related-Work Positioning

This repository is positioned as a small evidence package for inference-time
selection risk, not as a broad benchmark paper. It connects to three familiar
threads:

- Candidate reranking and inference-time selection methods, where the selected sample is an extreme
  order statistic under a model score.
- Model-based control and world-model evaluation, where imagined rollouts are
  useful only to the extent that their scores track downstream utility.
- Graph and object-structured dynamics, where the modeled structure can be
  locally plausible while omitting constraints that matter under execution.

The package contributes a finite-pool law and a controlled graph-physics
stress audit. It does not compare against external physics engines or large
world-model baselines, and it does not claim to settle which model class is
best. The reader-facing question is narrower: when a graph world model scores
its own imagined futures, how visible is selected-tail overfitting, and which
local controls catch it in this synthetic setting?

Evidence: `docs/claims.md`, `results/claims_status.md`, and
`results/claim_evidence_map.json`.

## Formal Setup

Let a finite candidate pool contain `m` candidates. Candidate `i` has internal
score `S_i` and real utility `U_i`. The candidate-budget selector draws `N` candidates with
replacement from the pool and selects a sampled candidate with maximal score.
If sampled candidates tie for maximal score, the selector breaks ties uniformly
among the tied sampled positions.

The setup separates score from utility. The score is the model-facing quantity
used to select. The utility is the evaluator-facing quantity used to judge the
selected candidate. In the graph-physics experiments, `S_i` is the imagined
graph score and `U_i` is the true-rollout utility.

### Theorem 1: Finite Score-Tie Selection Law

Partition the pool into exact score-tie groups `g`, ordered from highest score
to lowest score. Let `k_g` be the number of candidates in group `g`, let `b_g`
be the number of candidates with lower score than group `g`, and let
`mean(U | g)` be the mean real utility of candidates in group `g`. Then the
expected selected utility under top-score selection is

```text
E[U_selected] = sum_g p_g mean(U | g),
```

where

```text
p_g = ((k_g + b_g) / m)^N - (b_g / m)^N.
```

Evidence: implementation in `src/graph_constraint_tail_audit/theory.py`, tests in
`tests/test_theory.py`, empirical validation in
`results/tables/exact_law_validation.csv`, and visual validation in
`figures/figure3_exact_law_validation.png`.

### Interpretation

The theorem is independent of graph physics. It says that the selected group is
an order statistic under the score distribution. If high-score groups have low
mean real utility, larger `N` can make expected selected utility worse or can
leave it below the oracle tail even as selected score improves.

Evidence: the finite-law validation has mean absolute error `0.00134` across
140 validation rows in `results/tables/exact_law_validation.csv`.

## Graph-Physics Benchmark

The benchmark uses small mass-spring graph worlds generated on CPU. The
imagined simulator sees an imperfect graph. The real evaluator rolls out the
true graph, including hidden constraints and shifted dynamics.

Graph families:

- `ring_chord`
- `chain`
- `grid`
- `random_geometric`
- `clustered`

Hidden-failure modes:

- `omitted_edges`
- `shifted_rest_lengths`
- `delayed_damping`
- `topology_aliasing`
- `long_horizon_drift`

Stress levels:

- `mild`
- `medium`
- `severe`

Evidence: generator definitions in `src/graph_constraint_tail_audit/graph_physics.py`,
condition coverage in `results/run_summary.json`, stress aggregates in
`results/tables/stress_metrics.csv`, and family robustness in
`figures/figure10_family_robustness.png`.

### Candidate Score And Utility

Each candidate action sequence is rolled out under the imagined graph and the
true graph. The internal score rewards imagined target accuracy and gives a
small shortcut bonus:

```text
score = -imagined_target_error
        - 0.055 * imagined_observed_energy
        + shortcut_bonus.
```

The real utility penalizes true target error, hidden energy, observed energy,
action norm, and positive calibration gap:

```text
real_utility = -true_target_error
               - (0.48 + 0.11 * stress) * hidden_energy
               - 0.15 * true_observed_energy
               - 0.040 * action_norm
               - 0.09 * max(0, calibration_gap).
```

This explicit mismatch is the benchmark object. It is not presented as a
real-world robot reward; it is a controlled stress test for score/utility
alignment in graph-structured imagined rollouts.

Evidence: `src/graph_constraint_tail_audit/graph_physics.py` and
`results/tables/seed_metrics.csv`.

## Selectors

The selector suite is fixed and auditable in `selection.py`.

Raw selection chooses the candidate with maximal internal score. Oracle
selection chooses maximal real utility and is used only as an analysis upper
bound. Random selection samples a candidate uniformly and is used for gap
closure comparisons.

Repair scores subtract observable or proxy penalties from the raw score:

```text
observed_energy_ablation = score - 0.52 * observed_energy
action_penalty_ablation  = score - 0.16 * action_norm
calibration_gap_ablation = score - 0.32 * max(0, calibration_gap)
graph_energy_calibrated  = score - 0.34 * observed_energy - 0.08 * action_norm
constraint_probe         = score - 0.30 * hidden_risk_proxy
combined_repair          = score
                            - 0.36 * edge_violation
                            - 0.11 * action_norm
                            - 0.24 * max(0, calibration_gap)
                            - 0.10 * observed_energy
```

The hidden-risk proxy is:

```text
hidden_risk_proxy = edge_violation
                    + 0.30 * action_norm
                    + 0.35 * max(0, calibration_gap).
```

The adaptive gate compares raw and combined-repair selections. It blocks raw
selection for `N >= 8` when the raw selected candidate crosses a risk threshold
or when pilot-label evidence shows a repair gain. This gate is deliberately
described as pilot-label synthetic evidence, not as a deployable online safety
certificate.

Evidence: `src/graph_constraint_tail_audit/selection.py`,
`results/tables/ablation_metrics.csv`,
`results/tables/adaptive_gate_metrics.csv`, and
`results/tables/statistical_tests.csv`.

## Learned-Lite Calibration

The learned-lite component is a CPU NumPy ridge calibrator. It trains on
synthetic candidate rows and predicts real utility and hidden energy from
candidate features: raw score, imagined target error, observed energy, action
norm, calibration gap, graph size, edge counts, graph-family indicators,
hidden-failure indicators, and stress indicators.

The learned-safe rule uses the learned candidate only when the predicted
utility margin is large enough and predicted hidden energy is not worse than
the raw selected candidate by more than a small tolerance. This is a lightweight
calibration test, not a learned simulator claim.

Evidence: `src/graph_constraint_tail_audit/learned_model.py`,
`results/tables/learned_model_metrics.csv`,
`results/tables/learned_model_predictions.csv`, and
`figures/figure7_learned_model.png`.

## Experimental Protocol

The final bulletproof run uses:

- `N` values: `1, 2, 4, 8, 16, 32, 64`
- seeds: `0, 1, 2, 3`
- 80 graph-physics conditions
- 22,400 seed-level selector rows
- 5,600 aggregate rows
- 155 hard high-`N` cases where raw oracle gap exceeds `0.002`

Evidence: `results/run_summary.json`, `results/tables/seed_metrics.csv`, and
`results/tables/main_metrics.csv`.

The statistical tests compare paired raw selections against combined repair,
adaptive gate, and oracle on high-`N` cases. The hard-case subset is defined
only by raw oracle gap in the generated tables.

Evidence: `results/tables/statistical_tests.csv`.

## Results

### Headline Metrics

| Result | Value | Evidence |
| --- | ---: | --- |
| Conditions in final run | 80 | `results/run_summary.json` |
| Seed-level selector rows | 22,400 | `results/run_summary.json` |
| Exact-law mean absolute error | 0.00134 | `results/tables/exact_law_validation.csv` |
| Adaptive high-`N` gain over raw | 0.00701 | `results/tables/statistical_tests.csv` |
| Adaptive high-`N` 95% CI | [0.00529, 0.00893] | `results/tables/statistical_tests.csv` |
| Adaptive hard-case high-`N` gain | 0.01447 | `results/tables/statistical_tests.csv` |
| Adaptive hard-case 95% CI | [0.01119, 0.01812] | `results/tables/statistical_tests.csv` |
| Adaptive high-`N` negative deltas vs raw | 0 | `docs/final_audit.md` and `results/tables/statistical_tests.csv` |
| Raw-to-learned rank correlation | 0.756 to 0.932 | `results/tables/learned_model_metrics.csv` |
| Learned-safe hard-case oracle-gap closure | 0.588 | `results/tables/learned_model_metrics.csv` |

### Selected-Tail Failure

Raw top-score selection improves internal selected score as `N` grows, but the selected
candidate can remain below the oracle tail under real utility. The stress suite
shows this effect across graph families and hidden-failure modes rather than in
a single cherry-picked condition.

Evidence: `figures/figure1_selected_tail_failure.png`,
`figures/figure4_stress_heatmap.png`,
`figures/figure9_hidden_energy_by_n.png`,
`results/tables/main_metrics.csv`, and `results/tables/stress_metrics.csv`.

### Repair And Gate Behavior

Combined repair improves high-`N` selected real utility over raw selection by
`0.00594` on all high-`N` cases, with 95% CI `[0.00405, 0.00794]`. The
adaptive gate improves high-`N` selected real utility over raw selection by
`0.00701`, with 95% CI `[0.00529, 0.00893]`. On hard cases, adaptive gating
improves selected real utility by `0.01447`, with 95% CI
`[0.01119, 0.01812]`.

Evidence: `results/tables/statistical_tests.csv`,
`figures/figure5_ablation_components.png`,
`figures/figure6_adaptive_gate.png`, and
`figures/figure8_oracle_gap_closure.png`.

### Learned-Lite Calibration

The learned-lite ridge calibrator improves held-out rank correlation with real
utility from `0.756` for raw score to `0.932` for learned utility. The
learned-safe selector improves mean selected utility from `-0.1712` to
`-0.1634`, compared with oracle `-0.1621`, and closes `0.588` of the
hard-case oracle gap.

This supports only the narrow calibration claim. The learned-lite component is
CPU-local, synthetic, and not a broad learned-world-model result.

Evidence: `results/tables/learned_model_metrics.csv`,
`results/tables/learned_model_predictions.csv`, and
`figures/figure7_learned_model.png`.

## Figure Guide

- Figure 1, `figures/figure1_selected_tail_failure.png`: raw selected internal
  score and real utility as `N` grows.
- Figure 2, `figures/figure2_repair_comparison.png`: selector comparison at
  high `N`.
- Figure 3, `figures/figure3_exact_law_validation.png`: exact finite law versus
  Monte Carlo validation.
- Figure 4, `figures/figure4_stress_heatmap.png`: raw high-`N` oracle regret by
  graph family and hidden failure.
- Figure 5, `figures/figure5_ablation_components.png`: repair component
  ablations.
- Figure 6, `figures/figure6_adaptive_gate.png`: adaptive gate versus raw and
  repair.
- Figure 7, `figures/figure7_learned_model.png`: learned-lite calibration
  metrics.
- Figure 8, `figures/figure8_oracle_gap_closure.png`: oracle-gap closure by
  selector.
- Figure 9, `figures/figure9_hidden_energy_by_n.png`: hidden-energy behavior as
  `N` grows.
- Figure 10, `figures/figure10_family_robustness.png`: raw and adaptive
  selected utility across graph families.

## Table Guide

- `results/tables/main_metrics.csv`: aggregate metrics across all suites,
  selectors, and `N`.
- `results/tables/seed_metrics.csv`: seed-level selector rows used for paired
  comparisons.
- `results/tables/stress_metrics.csv`: stress-suite aggregates across graph
  families, hidden failures, and stress levels.
- `results/tables/repair_metrics.csv`: raw, repair, adaptive, and oracle
  selector aggregates.
- `results/tables/ablation_metrics.csv`: repair component ablation aggregates.
- `results/tables/adaptive_gate_metrics.csv`: seed-level adaptive-gate
  decisions and selected utilities.
- `results/tables/statistical_tests.csv`: paired deltas, confidence intervals,
  effect sizes, and improvement fractions.
- `results/tables/exact_law_validation.csv`: exact-law predictions, Monte Carlo
  estimates, and absolute errors.
- `results/tables/learned_model_metrics.csv`: learned-lite held-out summary.
- `results/tables/learned_model_predictions.csv`: held-out candidate-level
  learned-lite predictions.

## Limitations

The evidence is synthetic and CPU-local by design. It uses hand-coded graph
families, hand-coded hidden-failure modes, and a synthetic real utility. The
benchmark is useful because every mechanism is inspectable, but that same
inspectability limits external validity.

The adaptive gate uses pilot-label style synthetic evidence. Because the gate
can inspect repair gain under the synthetic evaluator, it should not be read as
an online deployment guarantee.

The learned-lite calibrator is a NumPy ridge model over synthetic candidate
features. It is useful as a calibration sanity check, not as evidence that a
large learned simulator would solve selected-tail risk.

The next meaningful tier would require external physics benchmarks or
real-system data. That tier is intentionally outside the current repository
scope.

Evidence: `docs/claims.md`, `results/claims_status.md`, and
`docs/final_audit.md`.

## Reproducibility Checklist

Run the commands from the repository root:

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
bash scripts/run_bulletproof.sh
bash scripts/run_claim_audit.sh
pytest
```

Expected pass criteria:

- `bash scripts/run_smoke.sh` completes and regenerates a small smoke artifact
  set.
- `bash scripts/run_all.sh` completes a broader local run.
- `bash scripts/run_bulletproof.sh` completes the final synthetic evidence run.
- `bash scripts/run_claim_audit.sh` exits successfully and reports no forbidden
  supported overclaims or missing required artifacts.
- `pytest` passes the theory, learned-model, graph-physics, and artifact-claim
  tests.

Publication audit:

- `docs/final_audit.md` records command outcomes, strongest artifacts, headline
  metrics, remaining limits, and publication status.
- `results/claim_evidence_map.json` maps manuscript claims to concrete
  artifacts.

## Claim Audit

Supported claims:

- C1: the finite tie-aware law predicts selected utility for finite
  graph-physics candidate pools.
  Evidence: `results/tables/exact_law_validation.csv`,
  `figures/figure3_exact_law_validation.png`, and `tests/test_theory.py`.
- C2: raw high-`N` graph-physics selection can expose selected-tail failure in
  controlled synthetic worlds.
  Evidence: `results/tables/stress_metrics.csv`,
  `figures/figure1_selected_tail_failure.png`, and
  `figures/figure4_stress_heatmap.png`.
- C3: repair components and combined repair improve selected-tail behavior in
  the synthetic stress suite.
  Evidence: `results/tables/ablation_metrics.csv`,
  `results/tables/statistical_tests.csv`, and
  `figures/figure5_ablation_components.png`.
- C4: a pilot-label adaptive gate improves high-`N` selection in the same
  controlled suite.
  Evidence: `results/tables/adaptive_gate_metrics.csv`,
  `results/tables/statistical_tests.csv`, and
  `figures/figure6_adaptive_gate.png`.
- C5: a CPU NumPy learned-lite calibrator improves held-out rank alignment in
  synthetic graph conditions.
  Evidence: `results/tables/learned_model_metrics.csv`,
  `results/tables/learned_model_predictions.csv`, and
  `figures/figure7_learned_model.png`.
- C6: the evidence spans multiple graph families, hidden-failure modes, and
  stress levels inside a CPU-local synthetic benchmark.
  Evidence: `results/tables/stress_metrics.csv`,
  `figures/figure10_family_robustness.png`, and `results/run_summary.json`.

Unsupported claims:

- C7: real-robot validation.
  Evidence: no real-robot experiment artifact is present.
- C8: broad benchmark superiority or state-of-the-art physics-model
  performance.
  Evidence: no external benchmark suite is present.
- C9: universal improvement from increasing `N`.
  Evidence: the manuscript studies selected-tail risk, not a universal
  monotonic-improvement theorem.
- C10: deployment safety beyond the controlled synthetic setting.
  Evidence: adaptive gating is pilot-label synthetic evidence only.

## Conclusion

Top-score graph-world selection is not merely "more samples." It is tail selection under a
score. In these controlled graph worlds, the tail can overfit the imagined
graph's physics: internal score improves while real utility remains below the
oracle tail. The finite law explains the selection mechanism, and the stress
suite shows that simple graph-aware repairs, pilot-label gating, and
learned-lite calibration reduce the mismatch within this narrow setting. The
result is submission-ready as a defensible synthetic evidence package, not as a
claim about real robots or broad benchmark dominance.

## Appendix A: Exact Law Derivation

Order exact score-tie groups from high score to low score. For group `g`, let
`k_g` be the number of candidates in the group and `b_g` be the number of
lower-scoring candidates. The group is selected exactly when every sampled
candidate is in `g` or below, and at least one sampled candidate is in `g`.

The probability that all `N` sampled candidates are in `g` or below is:

```text
((k_g + b_g) / m)^N.
```

The probability that all `N` sampled candidates are below `g` is:

```text
(b_g / m)^N.
```

Subtracting gives:

```text
p_g = ((k_g + b_g) / m)^N - (b_g / m)^N.
```

Conditional on group `g` being selected, the tie-breaking rule is symmetric
over sampled tied positions, and sampled members of `g` are exchangeable. The
expected utility after choosing from that group is therefore `mean(U | g)`.
Summing over groups gives:

```text
E[U_selected] = sum_g p_g mean(U | g).
```

Evidence: `src/graph_constraint_tail_audit/theory.py` and `tests/test_theory.py`.

## Appendix B: Benchmark Details

Each world starts from a graph layout, target displacement, velocities,
observed edges, hidden edges, rest lengths, damping, stiffness, and horizon
scale. Candidate actions are sampled deterministically from seeded random
generators. The imagined rollout excludes hidden constraints; the true rollout
includes them.

The final bulletproof configuration is recorded in `results/run_summary.json`:
`mode = bulletproof`, `N = [1, 2, 4, 8, 16, 32, 64]`, seeds `[0, 1, 2, 3]`,
80 conditions, and 22,400 seed-level selector rows.

Evidence: `experiments/run_experiments.py`,
`src/graph_constraint_tail_audit/graph_physics.py`, and
`results/run_summary.json`.

## Appendix C: Selector Definitions

The selector coefficients are fixed in code and reported in the main methods
section. The ablation table is the primary artifact for comparing component
roles; the statistical table is the primary artifact for paired high-`N`
deltas.

Evidence: `src/graph_constraint_tail_audit/selection.py`,
`results/tables/ablation_metrics.csv`, and
`results/tables/statistical_tests.csv`.

## Appendix D: Learned-Lite Calibration

The learned-lite model trains ridge regressors for real utility and hidden
energy. Training rows and held-out rows are synthetic candidate rows generated
from graph families, hidden failures, and stress levels. The model is evaluated
by MSE, rank correlation, selected utility, oracle-gap closure, safe use rate,
and negative-delta rate.

Evidence: `src/graph_constraint_tail_audit/learned_model.py`,
`results/tables/learned_model_metrics.csv`, and
`results/tables/learned_model_predictions.csv`.

## Appendix E: Artifact Map

The repository-level artifact map is `results/claim_evidence_map.json`. The
claim status generated by the audit is `results/claims_status.md` and
`results/claims_status.json`. The final publication-oriented audit is
`docs/final_audit.md`.

Evidence: `src/graph_constraint_tail_audit/audit.py`,
`results/claim_evidence_map.json`, `results/claims_status.md`, and
`docs/final_audit.md`.
