# When Graph Worlds Overfit Their Own Physics

## Abstract

Graph-structured world models often score imagined futures using only the constraints encoded in the learned or specified graph. We study a controlled failure mode for inference-time Best-of-N selection: as the number of sampled futures grows, the selected future can move into a high-score tail that exploits missing or miscalibrated graph constraints, improving internal score while leaving executed utility below the oracle tail. We give a finite tie-aware Best-of-N law for scored candidate pools, validate it empirically, and test graph-energy, action, calibration-gap, constraint-probe, combined-repair, adaptive-gating, and learned-lite calibration controls in a CPU-only synthetic mass-spring stress suite. The evidence is intentionally scoped to synthetic graph physics and does not claim real-robot or external benchmark validation.

## Problem

Best-of-N inference is attractive because it is simple: sample many candidate futures, score each candidate, and execute the best-scoring one. The risk is that the selected candidate is not typical. It is the upper tail under the model score, and that tail can be exactly where a graph world model is least faithful. In graph physics, common tail errors include omitted edges, shifted rest lengths, topology aliasing, delayed damping, and long-horizon drift.

This repo asks a bounded question: for fixed synthetic graph worlds and fixed scorers, when does sampling more graph-physics futures improve real utility, and when does it amplify model-specific scoring errors?

## Formal Setup

A finite candidate pool has real utilities `U_i` and internal scores `S_i`. Best-of-N samples `N` candidates with replacement and selects the candidate with maximal score, breaking exact score ties uniformly among tied sampled positions. The exact selected utility is the sum over score-tie groups:

`E[U_selected] = sum_g P(g selected) mean(U | g)`.

For a score group `g` with `k_g` candidates and `b_g` lower-scoring candidates in a pool of size `m`, the selected-group probability is:

`((k_g + b_g) / m)^N - (b_g / m)^N`.

This law is independent of graph physics. The graph experiments instantiate the utility and score arrays with candidate futures from controlled mass-spring graph worlds.

## Experimental Suite

The benchmark has five graph families:

- ring with chords
- chain
- grid
- random geometric graph
- clustered graph

It has five hidden-failure modes:

- omitted edges
- shifted rest lengths
- delayed damping
- topology aliasing
- long-horizon drift

It has three stress levels:

- mild
- medium
- severe

The imagined simulator sees an imperfect graph and emits a candidate score. The real evaluator rolls out the true graph and computes utility from target error, observed-edge energy, hidden-edge energy, action norm, and calibration gap.

## Selectors And Repairs

The selector suite includes:

- raw internal score
- observed-energy ablation
- action-penalty ablation
- calibration-gap ablation
- graph-energy calibrated score
- constraint-probe score
- combined repair score
- pilot-label adaptive gate
- random baseline
- oracle baseline

The adaptive gate is deliberately scoped: it is a pilot-label synthetic gate, not an online deployment guarantee. It blocks risky raw high-`N` selection when the selected candidate has high hidden-risk proxy or when pilot evidence shows repair gain.

## Learned-Lite Calibration

The learned-lite component is a CPU NumPy ridge calibrator. It learns from synthetic candidate features and predicts real utility and hidden energy on held-out graph conditions. This is not a large learned simulator. Its role is narrower: test whether lightweight learned calibration improves rank alignment between internal score and real utility.

## Evidence Artifacts

The strongest artifacts are:

- `results/tables/exact_law_validation.csv`
- `results/tables/stress_metrics.csv`
- `results/tables/ablation_metrics.csv`
- `results/tables/adaptive_gate_metrics.csv`
- `results/tables/learned_model_metrics.csv`
- `results/tables/statistical_tests.csv`
- `results/claim_evidence_map.json`
- `figures/figure1_selected_tail_failure.png`
- `figures/figure4_stress_heatmap.png`
- `figures/figure5_ablation_components.png`
- `figures/figure6_adaptive_gate.png`
- `figures/figure7_learned_model.png`
- `figures/figure10_family_robustness.png`

## Claims

Supported claims:

- The finite tie-aware law predicts selected utility in finite candidate pools.
- Raw high-`N` graph-physics selection can leave real utility below the oracle tail in controlled synthetic worlds.
- Repair components and combined repair improve selected-tail behavior in the synthetic stress suite.
- A pilot-label adaptive gate improves high-`N` selection in the same controlled suite.
- A CPU NumPy learned-lite calibrator improves held-out rank alignment in synthetic graph conditions.

Unsupported claims:

- real-robot validation
- state-of-the-art performance
- broad external benchmark superiority
- universal improvement from increasing `N`
- deployment safety beyond the controlled synthetic setting

## Reproducibility

Run:

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
bash scripts/run_bulletproof.sh
bash scripts/run_claim_audit.sh
pytest
```

The scripts regenerate tables, figures, JSON summaries, and claim audits. The final audit records command outcomes, artifact inventory, and publication status.

## Limitations

This is a synthetic graph-physics paper package. The next meaningful tier is external benchmark or real-system validation. That is intentionally outside the current repository scope. Within the CPU-local synthetic scope, the package is designed to be hard to attack: every supported claim is mapped to concrete artifacts, every unsupported claim is explicitly marked unsupported, and the claim audit fails on missing required evidence or forbidden overclaim language.
