# When Graph Worlds Overfit Their Own Physics

This repository studies **Best-of-N inference for graph-structured physics world models**. A model proposes future trajectories on a mass-spring graph, scores each imagined future with an internal graph-physics score, and executes the highest-scoring candidate. Real utility is evaluated by a separate simulator that includes hidden constraints, shifted rest lengths, topology aliasing, delayed damping, and long-horizon drift.

The central result is intentionally strict: in controlled CPU-local graph-physics settings, increasing `N` can improve selected internal score while leaving real utility below the oracle tail because the high-score tail exploits constraints the imagined graph does not faithfully represent. The repo then tests risk controls: graph-energy penalties, action penalties, calibration-gap penalties, constraint probes, combined repair, pilot-label adaptive gating, and a learned-lite NumPy calibrator.

## Quickstart

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
bash scripts/run_bulletproof.sh
bash scripts/run_claim_audit.sh
pytest
```

## What Is Included

- Exact finite tie-aware Best-of-N laws for scored finite candidate pools.
- A graph-physics stress suite over five graph families, five hidden-failure modes, and three stress levels.
- Selector ablations for each repair component plus combined repair, adaptive gating, random, and oracle baselines.
- Bootstrap confidence intervals, paired seed deltas, effect-size summaries, and oracle-gap closure metrics.
- A CPU NumPy learned-lite calibrator evaluated on held-out synthetic graph conditions.
- A claim audit that fails if supported claims lack required artifacts or contain forbidden overclaims.

## Main Artifacts

- `paper/paper.md`: full paper draft with theorem, experiments, ablations, limitations, and reproducibility checklist.
- `results/tables/stress_metrics.csv`: high-N behavior across graph families, hidden failures, and stress levels.
- `results/tables/ablation_metrics.csv`: repair-component and combined-repair evidence.
- `results/tables/adaptive_gate_metrics.csv`: adaptive-N gate decisions and selected utilities.
- `results/tables/learned_model_metrics.csv`: held-out learned-lite calibration evidence.
- `results/tables/statistical_tests.csv`: paired deltas, bootstrap CIs, and effect sizes.
- `results/claim_evidence_map.json`: supported claims mapped to concrete evidence artifacts.
- `figures/figure1_selected_tail_failure.png` through `figures/figure10_family_robustness.png`: the main figure suite.
- `docs/final_audit.md`: final validation, artifact inventory, remaining limits, commit, and publication audit.

## Headline Bulletproof Results

- 80 graph-physics conditions and 22,400 seed-level selector rows.
- Exact law mean absolute validation error: `0.00134`.
- Adaptive gate high-`N` gain over raw: `0.00701`, bootstrap 95% CI `[0.00529, 0.00893]`.
- Adaptive gate hard-case high-`N` gain over raw: `0.01447`, bootstrap 95% CI `[0.01119, 0.01812]`.
- Adaptive gate high-`N` negative deltas versus raw: `0`.
- Learned-lite rank correlation improves from `0.756` to `0.932`.
- Learned-safe calibration closes `0.588` of the hard-case oracle gap.

## Scope

This is a controlled synthetic graph-physics paper package. It is not a real-robot result, not an external physics-engine benchmark, not a state-of-the-art claim, and not evidence that larger `N` universally helps. Within the stated CPU-synthetic scope, the package is designed to leave no obvious meaningful improvement before moving to external benchmarks or real-system data.
