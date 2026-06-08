"""Run controlled graph-physics Best-of-N experiments."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from graph_physics_best_of_n.audit import write_claim_status, write_final_audit
from graph_physics_best_of_n.graph_physics import SCENARIOS, Candidate, generate_candidates, make_world
from graph_physics_best_of_n.selection import SELECTORS
from graph_physics_best_of_n.theory import law_validation_row


SELECTOR_ORDER = ["raw", "graph_energy_calibrated", "constraint_probe", "combined_repair", "random", "oracle"]


def _parse_ints(value: str | None, default: list[int]) -> list[int]:
    if value is None:
        return default
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def _selection_record(
    scenario: str,
    selector: str,
    n: int,
    seed: int,
    selected: Candidate,
    candidates: list[Candidate],
) -> dict[str, float | int | str]:
    oracle = max(candidates, key=lambda candidate: candidate.real_utility)
    return {
        "family": "controlled_graph_physics",
        "scenario": scenario,
        "selector": selector,
        "N": int(n),
        "seed": int(seed),
        "selected_score": float(selected.score),
        "selected_real_utility": float(selected.real_utility),
        "selected_true_target_error": float(selected.true_target_error),
        "selected_edge_violation": float(selected.edge_violation),
        "selected_hidden_energy": float(selected.hidden_energy),
        "selected_action_norm": float(selected.action_norm),
        "mean_candidate_score": float(np.mean([candidate.score for candidate in candidates])),
        "mean_candidate_real_utility": float(np.mean([candidate.real_utility for candidate in candidates])),
        "oracle_real_utility": float(oracle.real_utility),
        "oracle_regret": float(oracle.real_utility - selected.real_utility),
    }


def _aggregate(seed_df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "selected_score",
        "selected_real_utility",
        "selected_true_target_error",
        "selected_edge_violation",
        "selected_hidden_energy",
        "selected_action_norm",
        "oracle_regret",
    ]
    grouped = seed_df.groupby(["family", "scenario", "selector", "N"], as_index=False)
    mean_df = grouped[metrics].mean()
    sem_df = grouped[metrics].sem().fillna(0.0)
    sem_df = sem_df.rename(columns={metric: f"{metric}_sem" for metric in metrics})
    return mean_df.merge(sem_df, on=["family", "scenario", "selector", "N"])


def _deployment_gate(main: pd.DataFrame) -> str:
    raw = main[(main["scenario"] == "raw") & (main["selector"] == "raw")]
    repaired = main[(main["scenario"] == "raw") & (main["selector"] == "combined_repair")]
    if raw.empty or repaired.empty:
        return "insufficient_artifacts"
    high_n = int(raw["N"].max())
    raw_high = raw[raw["N"] == high_n].iloc[0]
    repaired_high = repaired[repaired["N"] == high_n].iloc[0]
    if repaired_high["selected_real_utility"] >= raw_high["selected_real_utility"] + 0.08:
        return "allow_high_n_with_combined_repair"
    return "block_high_n_without_repair"


def _write_figures(main: pd.DataFrame, law_df: pd.DataFrame, figures: Path) -> None:
    figures.mkdir(parents=True, exist_ok=True)

    raw = main[(main["scenario"] == "raw") & (main["selector"] == "raw")].sort_values("N")
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2))
    ax1.plot(raw["N"], raw["selected_score"], marker="o", color="#1f77b4", label="selected score")
    ax1.set_xscale("log", base=2)
    ax1.set_xlabel("N")
    ax1.set_ylabel("internal score", color="#1f77b4")
    ax2 = ax1.twinx()
    ax2.plot(raw["N"], raw["selected_real_utility"], marker="s", color="#c44e52", label="real utility")
    ax2.set_ylabel("real utility", color="#c44e52")
    ax1.set_title("Raw Best-of-N selected-tail failure")
    fig.tight_layout()
    fig.savefig(figures / "figure1_selected_tail_failure.png", dpi=160)
    plt.close(fig)

    high_n = int(main["N"].max())
    repair = main[(main["scenario"] == "raw") & (main["N"] == high_n)].copy()
    repair["selector"] = pd.Categorical(repair["selector"], SELECTOR_ORDER, ordered=True)
    repair = repair.sort_values("selector")
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ax.bar(repair["selector"].astype(str), repair["selected_real_utility"], color="#4c78a8")
    ax.set_ylabel("selected real utility")
    ax.set_title(f"Repair comparison at N={high_n}")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(figures / "figure2_repair_comparison.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    law = law_df.groupby("N", as_index=False)[["predicted_selected_utility", "empirical_selected_utility"]].mean()
    ax.plot(law["N"], law["predicted_selected_utility"], marker="o", label="exact")
    ax.plot(law["N"], law["empirical_selected_utility"], marker="s", label="Monte Carlo")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("N")
    ax.set_ylabel("selected real utility")
    ax.set_title("Finite law validation")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "figure3_exact_law_validation.png", dpi=160)
    plt.close(fig)


def run(root: Path, mode: str, ns: list[int], seeds: list[int]) -> dict[str, object]:
    start = time.time()
    results = root / "results"
    tables = results / "tables"
    figures = root / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    seed_rows: list[dict[str, float | int | str]] = []
    law_rows: list[dict[str, float | int | str]] = []
    trials = 600 if mode == "smoke" else 2200

    for seed in seeds:
        for scenario_index, scenario in enumerate(SCENARIOS):
            world = make_world(10_000 + 97 * seed + scenario_index, scenario=scenario)
            law_pool = generate_candidates(world, max(96, max(ns)), scenario=scenario, seed=seed * 11_003 + scenario_index)
            if scenario == "raw":
                for n in ns:
                    law_rows.append(
                        {
                            "scenario": scenario,
                            **law_validation_row(
                                [candidate.real_utility for candidate in law_pool],
                                [candidate.score for candidate in law_pool],
                                n=n,
                                trials=trials,
                                seed=seed + n * 31,
                            ),
                        }
                    )
            for n in ns:
                candidates = generate_candidates(world, n, scenario=scenario, seed=seed * 1009 + n * 37 + scenario_index)
                for selector_name in SELECTOR_ORDER:
                    selected = SELECTORS[selector_name](candidates, seed=seed + n)
                    seed_rows.append(_selection_record(scenario, selector_name, n, seed, selected, candidates))

    seed_df = pd.DataFrame(seed_rows)
    main = _aggregate(seed_df)
    law_df = pd.DataFrame(law_rows)
    repair_metrics = main[main["selector"].isin(SELECTOR_ORDER)].copy()

    seed_df.to_csv(tables / "seed_metrics.csv", index=False)
    main.to_csv(tables / "main_metrics.csv", index=False)
    repair_metrics.to_csv(tables / "repair_metrics.csv", index=False)
    law_df.to_csv(tables / "exact_law_validation.csv", index=False)

    _write_figures(main, law_df, figures)
    claims = write_claim_status(root)
    summary = {
        "mode": mode,
        "ns": ns,
        "seeds": seeds,
        "n_seed_rows": int(seed_df.shape[0]),
        "n_main_rows": int(main.shape[0]),
        "deployment_gate": _deployment_gate(main),
        "exact_law_mean_absolute_error": float(law_df["absolute_error"].mean()),
        "passes_claim_audit": claims["passes_claim_audit"],
        "runtime_seconds": round(time.time() - start, 3),
    }
    (results / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_final_audit(root, command_results={f"experiments --mode {mode}": "pass"})
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--root", default=Path.cwd())
    parser.add_argument("--ns", default=None)
    parser.add_argument("--seeds", default=None)
    args = parser.parse_args()

    default_ns = [1, 4, 16] if args.mode == "smoke" else [1, 2, 4, 8, 16, 32, 64]
    default_seeds = [0, 1] if args.mode == "smoke" else list(range(8))
    run(Path(args.root), args.mode, _parse_ints(args.ns, default_ns), _parse_ints(args.seeds, default_seeds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

