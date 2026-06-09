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
from graph_physics_best_of_n.graph_physics import (
    GRAPH_FAMILIES,
    HIDDEN_FAILURES,
    SCENARIO_BY_FAILURE,
    SCENARIOS,
    STRESS_LEVELS,
    Candidate,
    generate_candidates,
    make_world,
)
from graph_physics_best_of_n.learned_model import train_and_evaluate
from graph_physics_best_of_n.selection import SELECTORS
from graph_physics_best_of_n.stats import bootstrap_ci, paired_selector_summary
from graph_physics_best_of_n.theory import law_validation_row


SELECTOR_ORDER = [
    "raw",
    "observed_energy_ablation",
    "action_penalty_ablation",
    "calibration_gap_ablation",
    "graph_energy_calibrated",
    "constraint_probe",
    "combined_repair",
    "adaptive_gate",
    "random",
    "oracle",
]
REPAIR_SELECTORS = [
    "observed_energy_ablation",
    "action_penalty_ablation",
    "calibration_gap_ablation",
    "graph_energy_calibrated",
    "constraint_probe",
    "combined_repair",
    "adaptive_gate",
]


def _parse_ints(value: str | None, default: list[int]) -> list[int]:
    if value is None:
        return default
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def _mode_config(mode: str) -> dict[str, object]:
    if mode == "smoke":
        return {
            "ns": [1, 4, 16],
            "seeds": [0, 1],
            "families": ["ring_chord"],
            "failures": ["omitted_edges"],
            "stresses": ["medium"],
            "primary_scenarios": ["aligned", "raw"],
            "law_trials": 500,
            "learned_train": [],
            "learned_test": [],
        }
    if mode == "full":
        return {
            "ns": [1, 2, 4, 8, 16, 32, 64],
            "seeds": [0, 1, 2, 3],
            "families": ["ring_chord", "chain", "grid"],
            "failures": ["omitted_edges", "shifted_rest_lengths", "long_horizon_drift"],
            "stresses": ["mild", "medium"],
            "primary_scenarios": SCENARIOS,
            "law_trials": 1200,
            "learned_train": [0, 1],
            "learned_test": [20, 21],
        }
    return {
        "ns": [1, 2, 4, 8, 16, 32, 64],
            "seeds": [0, 1, 2, 3],
        "families": GRAPH_FAMILIES,
        "failures": HIDDEN_FAILURES,
        "stresses": STRESS_LEVELS,
        "primary_scenarios": SCENARIOS,
        "law_trials": 1800,
        "learned_train": [0, 1],
        "learned_test": [20, 21],
    }


def _primary_failure_for_scenario(scenario: str) -> str:
    return {
        "aligned": "omitted_edges",
        "edge_shortcut": "topology_aliasing",
        "hidden_constraint": "shifted_rest_lengths",
        "long_horizon": "long_horizon_drift",
        "raw": "omitted_edges",
    }[scenario]


def _conditions(config: dict[str, object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for scenario in config["primary_scenarios"]:  # type: ignore[index]
        rows.append(
            {
                "suite": "primary",
                "graph_family": "ring_chord",
                "hidden_failure": _primary_failure_for_scenario(str(scenario)),
                "stress_level": "medium",
                "scenario": str(scenario),
            }
        )
    for graph_family in config["families"]:  # type: ignore[index]
        for hidden_failure in config["failures"]:  # type: ignore[index]
            for stress_level in config["stresses"]:  # type: ignore[index]
                rows.append(
                    {
                        "suite": "stress",
                        "graph_family": str(graph_family),
                        "hidden_failure": str(hidden_failure),
                        "stress_level": str(stress_level),
                        "scenario": SCENARIO_BY_FAILURE[str(hidden_failure)],
                    }
                )
    return rows


def _selection_record(
    suite: str,
    selector: str,
    n: int,
    seed: int,
    selected: Candidate,
    candidates: list[Candidate],
) -> dict[str, float | int | str | bool]:
    oracle = max(candidates, key=lambda candidate: candidate.real_utility)
    mean_utility = float(np.mean([candidate.real_utility for candidate in candidates]))
    oracle_gap = float(oracle.real_utility - selected.real_utility)
    random_gap = float(oracle.real_utility - mean_utility)
    diagnostics = selected.diagnostics
    return {
        "suite": suite,
        "family": "controlled_graph_physics",
        "graph_family": selected.graph_family,
        "hidden_failure": selected.hidden_failure,
        "stress_level": selected.stress_level,
        "scenario": selected.scenario,
        "selector": selector,
        "N": int(n),
        "seed": int(seed),
        "selected_score": float(selected.score),
        "selected_real_utility": float(selected.real_utility),
        "selected_true_target_error": float(selected.true_target_error),
        "selected_edge_violation": float(selected.edge_violation),
        "selected_hidden_energy": float(selected.hidden_energy),
        "selected_action_norm": float(selected.action_norm),
        "selected_calibration_gap": float(selected.calibration_gap),
        "mean_candidate_score": float(np.mean([candidate.score for candidate in candidates])),
        "mean_candidate_real_utility": mean_utility,
        "oracle_real_utility": float(oracle.real_utility),
        "oracle_regret": oracle_gap,
        "oracle_gap_closed_vs_random": float(1.0 - oracle_gap / max(1e-9, random_gap)),
        "gate_decision": str(diagnostics.get("decision", "")),
        "gate_blocked_raw": bool(diagnostics.get("blocked_raw", False)),
        "gate_repair_gain": float(diagnostics.get("repair_gain", 0.0)),
        "gate_raw_risk": float(diagnostics.get("raw_risk", 0.0)),
    }


def _aggregate(seed_df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "selected_score",
        "selected_real_utility",
        "selected_true_target_error",
        "selected_edge_violation",
        "selected_hidden_energy",
        "selected_action_norm",
        "selected_calibration_gap",
        "oracle_regret",
        "oracle_gap_closed_vs_random",
    ]
    keys = ["suite", "family", "graph_family", "hidden_failure", "stress_level", "scenario", "selector", "N"]
    rows: list[dict[str, float | int | str]] = []
    for key_values, group in seed_df.groupby(keys):
        row = dict(zip(keys, key_values))
        for metric in metrics:
            values = group[metric].astype(float)
            lo, hi = bootstrap_ci(values, seed=len(rows) + len(metric), trials=500)
            row[metric] = float(values.mean())
            row[f"{metric}_sem"] = float(values.sem()) if values.shape[0] > 1 else 0.0
            row[f"{metric}_ci95_low"] = lo
            row[f"{metric}_ci95_high"] = hi
        rows.append(row)
    return pd.DataFrame(rows)


def _deployment_gate(main: pd.DataFrame) -> str:
    stress = main[(main["suite"] == "stress") & (main["N"] == main["N"].max())]
    raw = stress[stress["selector"] == "raw"]
    adaptive = stress[stress["selector"] == "adaptive_gate"]
    if raw.empty or adaptive.empty:
        return "insufficient_artifacts"
    joined = raw.merge(
        adaptive,
        on=["suite", "family", "graph_family", "hidden_failure", "stress_level", "scenario", "N"],
        suffixes=("_raw", "_adaptive"),
    )
    gain = float((joined["selected_real_utility_adaptive"] - joined["selected_real_utility_raw"]).mean())
    return "allow_high_n_with_adaptive_gate" if gain >= 0.001 else "block_high_n_until_gate_improves"


def _write_required_plot(figures: Path, name: str, draw_fn) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    draw_fn(fig, ax)
    fig.tight_layout()
    fig.savefig(figures / name, dpi=170)
    plt.close(fig)


def _write_figures(main: pd.DataFrame, law_df: pd.DataFrame, learned_summary: pd.DataFrame, figures: Path) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    high_n = int(main["N"].max())

    def figure1(fig, ax):
        raw = main[(main["suite"] == "primary") & (main["scenario"] == "raw") & (main["selector"] == "raw")].sort_values("N")
        ax.plot(raw["N"], raw["selected_score"], marker="o", color="#1f77b4", label="selected score")
        ax.set_xscale("log", base=2)
        ax.set_xlabel("N")
        ax.set_ylabel("internal score", color="#1f77b4")
        ax2 = ax.twinx()
        ax2.plot(raw["N"], raw["selected_real_utility"], marker="s", color="#c44e52", label="real utility")
        ax2.set_ylabel("real utility", color="#c44e52")
        ax.set_title("Raw selected-tail failure")

    _write_required_plot(figures, "figure1_selected_tail_failure.png", figure1)

    def figure2(fig, ax):
        repair = main[(main["suite"] == "primary") & (main["scenario"] == "raw") & (main["N"] == high_n)].copy()
        repair["selector"] = pd.Categorical(repair["selector"], SELECTOR_ORDER, ordered=True)
        repair = repair.sort_values("selector")
        ax.bar(repair["selector"].astype(str), repair["selected_real_utility"], color="#4c78a8")
        ax.set_ylabel("selected real utility")
        ax.set_title(f"Selector comparison at N={high_n}")
        ax.tick_params(axis="x", rotation=30)

    _write_required_plot(figures, "figure2_repair_comparison.png", figure2)

    def figure3(fig, ax):
        law = law_df.groupby("N", as_index=False)[["predicted_selected_utility", "empirical_selected_utility"]].mean()
        ax.plot(law["N"], law["predicted_selected_utility"], marker="o", label="exact")
        ax.plot(law["N"], law["empirical_selected_utility"], marker="s", label="Monte Carlo")
        ax.set_xscale("log", base=2)
        ax.set_xlabel("N")
        ax.set_ylabel("selected real utility")
        ax.set_title("Finite law validation")
        ax.legend()

    _write_required_plot(figures, "figure3_exact_law_validation.png", figure3)

    def figure4(fig, ax):
        stress = main[(main["suite"] == "stress") & (main["selector"] == "raw") & (main["N"] == high_n)]
        pivot = stress.pivot_table(index="hidden_failure", columns="graph_family", values="oracle_regret", aggfunc="mean").reindex(
            index=HIDDEN_FAILURES, columns=GRAPH_FAMILIES
        )
        image = ax.imshow(pivot.fillna(0.0).to_numpy(), aspect="auto", cmap="magma")
        ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=30, ha="right")
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        ax.set_title("Raw high-N oracle regret by stress condition")
        fig.colorbar(image, ax=ax, label="oracle regret")

    _write_required_plot(figures, "figure4_stress_heatmap.png", figure4)

    def figure5(fig, ax):
        ablation = main[(main["suite"] == "primary") & (main["scenario"] == "raw") & (main["N"] == high_n)]
        selectors = ["raw"] + REPAIR_SELECTORS
        values = [float(ablation[ablation["selector"] == selector]["selected_real_utility"].mean()) for selector in selectors]
        ax.bar(selectors, values, color="#59a14f")
        ax.set_ylabel("selected real utility")
        ax.set_title("Repair component ablations")
        ax.tick_params(axis="x", rotation=30)

    _write_required_plot(figures, "figure5_ablation_components.png", figure5)

    def figure6(fig, ax):
        gate = main[(main["suite"] == "stress") & (main["N"] == high_n) & (main["selector"].isin(["raw", "adaptive_gate", "combined_repair"]))]
        pivot = gate.groupby("selector")["selected_real_utility"].mean().reindex(["raw", "adaptive_gate", "combined_repair"])
        ax.bar(pivot.index.astype(str), pivot.values, color="#b07aa1")
        ax.set_ylabel("selected real utility")
        ax.set_title("Adaptive-N gate versus raw and repair")

    _write_required_plot(figures, "figure6_adaptive_gate.png", figure6)

    def figure7(fig, ax):
        if learned_summary.empty:
            ax.text(0.5, 0.5, "learned-lite skipped in smoke mode", ha="center", va="center")
            ax.set_axis_off()
            return
        row = learned_summary.iloc[0]
        labels = ["raw rank", "learned rank", "safe gap closed"]
        values = [
            row["raw_score_rank_correlation"],
            row["learned_utility_rank_correlation"],
            row["hard_case_safe_gap_closed"],
        ]
        ax.bar(labels, values, color=["#9c755f", "#4e79a7", "#59a14f"])
        ax.set_ylim(min(0.0, min(values) - 0.05), max(values) + 0.1)
        ax.set_ylabel("held-out metric")
        ax.set_title("Learned-lite safe calibration")

    _write_required_plot(figures, "figure7_learned_model.png", figure7)

    def figure8(fig, ax):
        stress = main[(main["suite"] == "stress") & (main["N"] == high_n)]
        pivot = stress.groupby("selector")["oracle_gap_closed_vs_random"].mean().reindex(SELECTOR_ORDER)
        ax.bar(pivot.index.astype(str), pivot.values, color="#f28e2b")
        ax.set_ylabel("oracle gap closed vs random")
        ax.set_title("Oracle-gap closure")
        ax.tick_params(axis="x", rotation=30)

    _write_required_plot(figures, "figure8_oracle_gap_closure.png", figure8)

    def figure9(fig, ax):
        raw = main[(main["suite"] == "primary") & (main["scenario"] == "raw") & (main["selector"].isin(["raw", "combined_repair", "adaptive_gate"]))]
        for selector, group in raw.groupby("selector"):
            group = group.sort_values("N")
            ax.plot(group["N"], group["selected_hidden_energy"], marker="o", label=selector)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("N")
        ax.set_ylabel("selected hidden energy")
        ax.set_title("Hidden-energy amplification")
        ax.legend()

    _write_required_plot(figures, "figure9_hidden_energy_by_n.png", figure9)

    def figure10(fig, ax):
        stress = main[(main["suite"] == "stress") & (main["N"] == high_n) & (main["selector"].isin(["raw", "adaptive_gate"]))]
        pivot = stress.pivot_table(index="graph_family", columns="selector", values="selected_real_utility", aggfunc="mean").reindex(
            GRAPH_FAMILIES
        )
        width = 0.35
        x = np.arange(len(pivot.index))
        ax.bar(x - width / 2, pivot.get("raw", pd.Series(0.0, index=pivot.index)), width, label="raw")
        ax.bar(x + width / 2, pivot.get("adaptive_gate", pd.Series(0.0, index=pivot.index)), width, label="adaptive")
        ax.set_xticks(x, pivot.index, rotation=25, ha="right")
        ax.set_ylabel("selected real utility")
        ax.set_title("Family robustness")
        ax.legend()

    _write_required_plot(figures, "figure10_family_robustness.png", figure10)


def _run_condition(
    condition: dict[str, str],
    seed: int,
    ns: list[int],
    selectors: list[str],
    law_trials: int,
) -> tuple[list[dict[str, float | int | str | bool]], list[dict[str, float | int | str]]]:
    world = make_world(
        10_000 + seed * 97 + len(condition["graph_family"]) * 13 + len(condition["hidden_failure"]),
        scenario=condition["scenario"],
        graph_family=condition["graph_family"],
        hidden_failure=condition["hidden_failure"],
        stress_level=condition["stress_level"],
    )
    max_n = max(ns)
    pool = generate_candidates(world, max_n, seed=seed * 1009 + len(condition["scenario"]) * 37)
    rows: list[dict[str, float | int | str | bool]] = []
    law_rows: list[dict[str, float | int | str]] = []
    for n in ns:
        candidates = pool[:n]
        for selector_name in selectors:
            selected = SELECTORS[selector_name](candidates, seed=seed + n)
            rows.append(_selection_record(condition["suite"], selector_name, n, seed, selected, candidates))
        if condition["scenario"] == "raw" and condition["graph_family"] in {"ring_chord", "grid"} and condition["stress_level"] != "severe":
            law_rows.append(
                {
                    "suite": condition["suite"],
                    "graph_family": condition["graph_family"],
                    "hidden_failure": condition["hidden_failure"],
                    "stress_level": condition["stress_level"],
                    "seed": seed,
                    **law_validation_row(
                        [candidate.real_utility for candidate in pool],
                        [candidate.score for candidate in pool],
                        n=n,
                        trials=law_trials,
                        seed=seed + n * 31,
                    ),
                }
            )
    return rows, law_rows


def _write_claim_evidence_map(root: Path) -> None:
    payload = {
        "C1_exact_finite_law": ["results/tables/exact_law_validation.csv", "figures/figure3_exact_law_validation.png", "tests/test_theory.py"],
        "C2_selected_tail_failure": ["results/tables/stress_metrics.csv", "figures/figure1_selected_tail_failure.png", "figures/figure4_stress_heatmap.png"],
        "C3_repairs_and_ablation": ["results/tables/ablation_metrics.csv", "figures/figure5_ablation_components.png"],
        "C4_adaptive_gate": ["results/tables/adaptive_gate_metrics.csv", "figures/figure6_adaptive_gate.png"],
        "C5_learned_lite_calibration": ["results/tables/learned_model_metrics.csv", "figures/figure7_learned_model.png"],
        "C6_scope_limits": ["docs/claims.md", "paper/paper.md", "docs/final_audit.md"],
    }
    (root / "results" / "claim_evidence_map.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run(root: Path, mode: str, ns: list[int] | None = None, seeds: list[int] | None = None) -> dict[str, object]:
    start = time.time()
    config = _mode_config(mode)
    ns = ns or list(config["ns"])  # type: ignore[arg-type]
    seeds = seeds or list(config["seeds"])  # type: ignore[arg-type]
    results = root / "results"
    tables = results / "tables"
    figures = root / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    seed_rows: list[dict[str, float | int | str | bool]] = []
    law_rows: list[dict[str, float | int | str]] = []
    conditions = _conditions(config)
    for seed in seeds:
        for condition in conditions:
            rows, laws = _run_condition(condition, seed, ns, SELECTOR_ORDER, int(config["law_trials"]))
            seed_rows.extend(rows)
            law_rows.extend(laws)

    seed_df = pd.DataFrame(seed_rows)
    main = _aggregate(seed_df)
    law_df = pd.DataFrame(law_rows)
    stress_metrics = main[main["suite"] == "stress"].copy()
    repair_metrics = main[main["selector"].isin(REPAIR_SELECTORS + ["raw", "oracle"])].copy()
    ablation_metrics = main[main["selector"].isin(["raw"] + REPAIR_SELECTORS)].copy()
    adaptive_gate_metrics = seed_df[seed_df["selector"] == "adaptive_gate"].copy()

    high_filter = {"N": max(ns)}
    high_filter = {"N": max(ns)}
    keys = ["suite", "graph_family", "hidden_failure", "stress_level", "scenario", "N", "seed"]
    raw_high = seed_df[(seed_df["selector"] == "raw") & (seed_df["N"] == max(ns))][keys + ["oracle_regret"]].rename(
        columns={"oracle_regret": "raw_oracle_regret"}
    )
    with_raw_gap = seed_df.merge(raw_high, on=keys, how="left")
    hard_seed_df = with_raw_gap[with_raw_gap["raw_oracle_regret"] > 0.002].copy()
    hard_case_count = int(hard_seed_df[keys].drop_duplicates().shape[0])

    statistical_tests = pd.concat(
        [
            paired_selector_summary(seed_df, "raw", ["combined_repair", "adaptive_gate", "oracle"], "selected_real_utility", high_filter, scope="all_high_n"),
            paired_selector_summary(seed_df, "raw", ["combined_repair", "adaptive_gate"], "oracle_regret", high_filter, scope="all_high_n"),
            paired_selector_summary(
                hard_seed_df,
                "raw",
                ["combined_repair", "adaptive_gate", "oracle"],
                "selected_real_utility",
                high_filter,
                scope="hard_oracle_gap_gt_0.002",
            ),
            paired_selector_summary(
                hard_seed_df,
                "raw",
                ["combined_repair", "adaptive_gate"],
                "oracle_regret",
                high_filter,
                scope="hard_oracle_gap_gt_0.002",
            ),
        ],
        ignore_index=True,
    )

    learned_train = list(config["learned_train"])  # type: ignore[arg-type]
    learned_test = list(config["learned_test"])  # type: ignore[arg-type]
    if learned_train and learned_test:
        learned_summary, learned_rows = train_and_evaluate(learned_train, learned_test)
    else:
        learned_summary = pd.DataFrame()
        learned_rows = pd.DataFrame()

    seed_df.to_csv(tables / "seed_metrics.csv", index=False)
    main.to_csv(tables / "main_metrics.csv", index=False)
    stress_metrics.to_csv(tables / "stress_metrics.csv", index=False)
    repair_metrics.to_csv(tables / "repair_metrics.csv", index=False)
    ablation_metrics.to_csv(tables / "ablation_metrics.csv", index=False)
    adaptive_gate_metrics.to_csv(tables / "adaptive_gate_metrics.csv", index=False)
    law_df.to_csv(tables / "exact_law_validation.csv", index=False)
    statistical_tests.to_csv(tables / "statistical_tests.csv", index=False)
    learned_summary.to_csv(tables / "learned_model_metrics.csv", index=False)
    learned_rows.to_csv(tables / "learned_model_predictions.csv", index=False)

    _write_figures(main, law_df, learned_summary, figures)
    _write_claim_evidence_map(root)
    claims = write_claim_status(root)
    summary = {
        "mode": mode,
        "ns": ns,
        "seeds": seeds,
        "n_conditions": len(conditions),
        "n_seed_rows": int(seed_df.shape[0]),
        "n_main_rows": int(main.shape[0]),
        "n_hard_high_n_cases": hard_case_count,
        "deployment_gate": _deployment_gate(main),
        "exact_law_mean_absolute_error": float(law_df["absolute_error"].mean()) if not law_df.empty else None,
        "learned_lite_ran": bool(not learned_summary.empty),
        "passes_claim_audit": claims["passes_claim_audit"],
        "runtime_seconds": round(time.time() - start, 3),
    }
    (results / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_final_audit(root, command_results={f"experiments --mode {mode}": "pass"})
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full", "bulletproof"], default="smoke")
    parser.add_argument("--root", default=Path.cwd())
    parser.add_argument("--ns", default=None)
    parser.add_argument("--seeds", default=None)
    args = parser.parse_args()

    config = _mode_config(args.mode)
    ns = _parse_ints(args.ns, list(config["ns"]))  # type: ignore[arg-type]
    seeds = _parse_ints(args.seeds, list(config["seeds"]))  # type: ignore[arg-type]
    run(Path(args.root), args.mode, ns=ns, seeds=seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
