# When Graph Worlds Overfit Their Own Physics

This repository studies **Best-of-N inference for graph-structured physics world models**. A model proposes future trajectories on a mass-spring graph, scores each imagined future with an internal graph-physics score, and executes the highest-scoring candidate. Real utility is evaluated by a separate simulator that includes hidden constraints and long-horizon energy.

The core claim is narrow: in controlled CPU toy graph-physics settings, increasing `N` can raise selected internal score while selected real utility stagnates or falls, because the high-score tail exploits missing or miscalibrated graph constraints. Lightweight graph-energy checks and constraint probes can recover much of the selected-tail utility in these synthetic regimes.

## Quickstart

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
bash scripts/run_claim_audit.sh
pytest
```

## What Is Included

- Exact finite tie-aware Best-of-N selection laws for scored finite candidate pools.
- A deterministic graph-physics toy world with observed and hidden spring constraints.
- Synthetic experiments for raw selection, graph-energy calibration, constraint probing, combined repair, random selection, and oracle selection.
- Claim and artifact audits that separate supported synthetic claims from unsupported broader claims.

## Main Artifacts

- `results/tables/main_metrics.csv`: aggregated selected score, real utility, graph energy, and violation metrics.
- `results/tables/exact_law_validation.csv`: exact-vs-Monte-Carlo validation of the finite Best-of-N law.
- `figures/figure1_selected_tail_failure.png`: selected-score increase versus real-utility degradation.
- `figures/figure2_repair_comparison.png`: repair selector comparison.
- `figures/figure3_exact_law_validation.png`: exact law validation plot.
- `results/claims_status.json`: machine-readable claim audit.
- `docs/final_audit.md`: final validation and publishing audit.

## Scope

This is a graph-physics toy benchmark, not a real robot result, not a broad physics-engine benchmark, and not evidence of universal Best-of-N improvement. The evidence supports controlled synthetic claims only.

