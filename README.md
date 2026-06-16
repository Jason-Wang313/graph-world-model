# Constraint Shadows in Graph World Models

This repository is a submission-oriented evidence package for **constraint-shadow audits in graph-structured physics world models**. A model proposes future trajectories on a mass-spring graph, scores each imagined future with an internal graph-physics score, and executes the highest-scoring candidate. Real utility is evaluated by a separate simulator that includes hidden constraints, shifted rest lengths, topology aliasing, delayed damping, and long-horizon drift.

The central result is intentionally strict: in controlled CPU-local graph-physics settings, increasing `N` can improve selected internal score while leaving real utility below the oracle tail because the high-score tail exploits constraints the imagined graph does not faithfully represent. The repo then tests risk controls: graph-energy penalties, action penalties, calibration-gap penalties, constraint probes, combined repair, pilot-label adaptive gating, and a learned-lite NumPy calibrator. Every supported manuscript claim is mapped to concrete CSVs, figures, tests, or audit artifacts.

## Quickstart

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
bash scripts/run_bulletproof.sh
bash scripts/run_claim_audit.sh
pytest
```

## What Is Included

- Exact finite score-tie laws for top-score candidate selection in finite pools.
- A graph-physics stress suite over five graph families, five hidden-failure modes, and three stress levels.
- Selector ablations for each repair component plus combined repair, adaptive gating, random, and oracle baselines.
- Bootstrap confidence intervals, paired seed deltas, effect-size summaries, and oracle-gap closure metrics.
- A CPU NumPy learned-lite calibrator evaluated on held-out synthetic graph conditions.
- A claim audit that fails if supported claims lack required artifacts or contain forbidden overclaims.

## Main Artifacts

- `paper/iclr/main.tex`: primary ICLR-style LaTeX manuscript, using the official ICLR 2026 template files under `paper/iclr/`.
- `paper/iclr/references.bib`: verified bibliography for the ICLR manuscript.
- `paper/paper.md`: audit/source companion with title, abstract, related-work positioning, formal setup, theorem, methods, experiments, results, limitations, reproducibility checklist, and appendices.
- `results/tables/stress_metrics.csv`: high-N behavior across graph families, hidden failures, and stress levels.
- `results/tables/ablation_metrics.csv`: repair-component and combined-repair evidence.
- `results/tables/adaptive_gate_metrics.csv`: adaptive-N gate decisions and selected utilities.
- `results/tables/learned_model_metrics.csv`: held-out learned-lite calibration evidence.
- `results/tables/statistical_tests.csv`: paired deltas, bootstrap CIs, and effect sizes.
- `results/claim_evidence_map.json`: supported and explicitly unsupported claims mapped to evidence artifacts or absence-of-evidence notes.
- `figures/figure1_selected_tail_failure.png` through `figures/figure10_family_robustness.png`: the main figure suite.
- `docs/final_audit.md`: final validation, artifact inventory, remaining limits, commit, and publication audit.

## ICLR Paper Build

```bash
python scripts/build_v4_paper.py
python scripts/run_v4_claim_audit.py
python -m pytest -q
```

The v4 builder regenerates the low-RAM evidence cache, runs the claim audit, compiles the ICLR PDF, writes `paper/final/graph world model-v4.pdf`, copies the same PDF to the Desktop, and removes stale v2/v3 Desktop copies. The final audit checks hashes, source-map routing, claim gates, generated figures, page count, and LaTeX blockers.

## Final V4 Package

- Final PDF: `paper/final/graph world model-v4.pdf` and Desktop `graph world model-v4.pdf`.
- V4 cache: `results/v4_frozen_evidence/`.
- V4 figures: `results/figures/v4/`.
- Claim gates: `10/10` pass.
- Benchmark protocol bridge: `5` recognized graph-dynamics probe rows, `5` pass rows.
- Aggregate stress gates: adaptive gating is non-worse in `75/75` cell-level stress rows.
- Supported/unsupported ledger: `7` supported claims and `4` explicit unsupported boundaries.

## Claim Discipline

- Supported: finite tie-aware law, selected-tail failure in synthetic graph physics, repair/gate improvements inside the stress suite, learned-lite held-out calibration, multi-family synthetic coverage, and v4 recognized graph-dynamics probe rows.
- Unsupported: real-robot validation, broad external-dataset superiority, reproduced SOTA performance, universal improvement from increasing `N`, and deployment safety beyond the controlled synthetic setting.
- Audit: `bash scripts/run_claim_audit.sh` regenerates claim status and fails on missing required artifacts or forbidden supported overclaims.

## Headline Bulletproof Results

- 80 graph-physics conditions and 22,400 seed-level selector rows.
- Exact law mean absolute validation error: `0.00134`.
- Adaptive gate high-`N` gain over raw: `0.00701`, bootstrap 95% CI `[0.00529, 0.00893]`.
- Adaptive gate hard-case high-`N` gain over raw: `0.01447`, bootstrap 95% CI `[0.01119, 0.01812]`.
- Adaptive gate high-`N` negative deltas versus raw: `0`.
- Learned-lite rank correlation improves from `0.756` to `0.932`.
- Learned-safe calibration closes `0.588` of the hard-case oracle gap.
- V4 claim gates: `10/10`; benchmark-protocol pass rows: `5/5`; adaptive non-worse stress cells: `75/75`.

## Scope

This is a controlled synthetic graph-physics paper package. V4 adds recognized graph-dynamics protocol probes, but it is still not a real-robot result, not an external held-out dataset result, not a reproduced SOTA claim, and not evidence that larger `N` universally helps. Within the stated CPU-synthetic scope, the package is designed to leave no obvious meaningful improvement before moving to external benchmarks or real-system data.
