"""CPU-only learned-lite calibration evidence for graph-physics candidates."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .graph_physics import GRAPH_FAMILIES, HIDDEN_FAILURES, STRESS_LEVELS, SCENARIO_BY_FAILURE, generate_candidates, make_world
from .stats import rank_correlation


@dataclass(frozen=True)
class RidgeModel:
    weights: np.ndarray
    feature_mean: np.ndarray
    feature_std: np.ndarray


def _candidate_features(row: dict[str, float | int | str]) -> list[float]:
    features = [
        float(row["score"]),
        float(row["imagined_target_error"]),
        float(row["observed_energy"]),
        float(row["action_norm"]),
        float(row["calibration_gap"]),
        float(row["n_nodes"]),
        float(row["n_imagined_edges"]),
        float(row["n_hidden_edges"]),
    ]
    graph = str(row["graph_family"])
    failure = str(row["hidden_failure"])
    stress = str(row["stress_level"])
    features.extend(1.0 if graph == name else 0.0 for name in GRAPH_FAMILIES)
    features.extend(1.0 if failure == name else 0.0 for name in HIDDEN_FAILURES)
    features.extend(1.0 if stress == name else 0.0 for name in STRESS_LEVELS)
    return features


def candidate_row(world_seed: int, candidate_seed: int, graph_family: str, hidden_failure: str, stress_level: str) -> list[dict[str, float | int | str]]:
    scenario = SCENARIO_BY_FAILURE[hidden_failure]
    world = make_world(
        world_seed,
        scenario=scenario,
        graph_family=graph_family,
        hidden_failure=hidden_failure,
        stress_level=stress_level,
    )
    rows: list[dict[str, float | int | str]] = []
    for index, candidate in enumerate(generate_candidates(world, 32, seed=candidate_seed)):
        rows.append(
            {
                "candidate_index": index,
                "graph_family": graph_family,
                "hidden_failure": hidden_failure,
                "stress_level": stress_level,
                "world_seed": world_seed,
                "score": candidate.score,
                "real_utility": candidate.real_utility,
                "imagined_target_error": candidate.imagined_target_error,
                "observed_energy": candidate.observed_energy,
                "hidden_energy": candidate.hidden_energy,
                "action_norm": candidate.action_norm,
                "calibration_gap": candidate.calibration_gap,
                "n_nodes": int(world.positions.shape[0]),
                "n_imagined_edges": int(len(world.imagined_edges)),
                "n_hidden_edges": int(len(world.hidden_edges)),
            }
        )
    return rows


def make_candidate_dataset(seeds: list[int]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for seed in seeds:
        for graph_family in GRAPH_FAMILIES:
            for hidden_failure in HIDDEN_FAILURES:
                for stress_level in STRESS_LEVELS:
                    rows.extend(candidate_row(50_000 + seed * 101, 70_000 + seed * 1_009, graph_family, hidden_failure, stress_level))
    return pd.DataFrame(rows)


def _design_matrix(df: pd.DataFrame) -> np.ndarray:
    return np.asarray([_candidate_features(row) for row in df.to_dict("records")], dtype=float)


def fit_ridge(df: pd.DataFrame, target: str, l2: float = 1e-2) -> RidgeModel:
    x = _design_matrix(df)
    y = df[target].to_numpy(dtype=float)
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0.0] = 1.0
    z = (x - mean) / std
    z = np.column_stack([np.ones(z.shape[0]), z])
    penalty = np.eye(z.shape[1]) * l2
    penalty[0, 0] = 0.0
    weights = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return RidgeModel(weights=weights, feature_mean=mean, feature_std=std)


def predict(model: RidgeModel, df: pd.DataFrame) -> np.ndarray:
    x = _design_matrix(df)
    z = (x - model.feature_mean) / model.feature_std
    z = np.column_stack([np.ones(z.shape[0]), z])
    return z @ model.weights


def train_and_evaluate(train_seeds: list[int], test_seeds: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = make_candidate_dataset(train_seeds)
    test = make_candidate_dataset(test_seeds)
    utility_model = fit_ridge(train, "real_utility")
    hidden_model = fit_ridge(train, "hidden_energy")
    test = test.copy()
    test["learned_utility"] = predict(utility_model, test)
    test["learned_hidden_energy"] = predict(hidden_model, test)

    raw_mse = float(np.mean((test["score"] - test["real_utility"]) ** 2))
    learned_mse = float(np.mean((test["learned_utility"] - test["real_utility"]) ** 2))
    hidden_mse = float(np.mean((test["learned_hidden_energy"] - test["hidden_energy"]) ** 2))
    raw_rank = rank_correlation(test["score"], test["real_utility"])
    learned_rank = rank_correlation(test["learned_utility"], test["real_utility"])

    group_cols = ["graph_family", "hidden_failure", "stress_level", "world_seed"]
    selector_rows = []
    for _, group in test.groupby(group_cols):
        raw = group.loc[group["score"].idxmax()]
        learned = group.loc[group["learned_utility"].idxmax()]
        oracle = group.loc[group["real_utility"].idxmax()]
        selector_rows.append(
            {
                "raw_selected_utility": float(raw["real_utility"]),
                "learned_selected_utility": float(learned["real_utility"]),
                "oracle_selected_utility": float(oracle["real_utility"]),
                "oracle_gap_closed": float(
                    (learned["real_utility"] - raw["real_utility"])
                    / max(1e-9, oracle["real_utility"] - raw["real_utility"])
                ),
            }
        )
    selector_df = pd.DataFrame(selector_rows)
    summary = pd.DataFrame(
        [
            {
                "train_rows": int(train.shape[0]),
                "test_rows": int(test.shape[0]),
                "raw_score_mse_to_utility": raw_mse,
                "learned_utility_mse": learned_mse,
                "learned_hidden_energy_mse": hidden_mse,
                "raw_score_rank_correlation": raw_rank,
                "learned_utility_rank_correlation": learned_rank,
                "mean_raw_selected_utility": float(selector_df["raw_selected_utility"].mean()),
                "mean_learned_selected_utility": float(selector_df["learned_selected_utility"].mean()),
                "mean_oracle_selected_utility": float(selector_df["oracle_selected_utility"].mean()),
                "mean_oracle_gap_closed": float(np.clip(selector_df["oracle_gap_closed"], -1.0, 1.0).mean()),
            }
        ]
    )
    return summary, test
