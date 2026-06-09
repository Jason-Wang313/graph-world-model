"""Small statistical helpers for CPU-only experiment audits."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def bootstrap_ci(values: Iterable[float], seed: int = 0, trials: int = 1000, alpha: float = 0.05) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan")
    if arr.size == 1:
        value = float(arr[0])
        return value, value
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, arr.size, size=(trials, arr.size))
    means = arr[indices].mean(axis=1)
    lo = float(np.quantile(means, alpha / 2.0))
    hi = float(np.quantile(means, 1.0 - alpha / 2.0))
    return lo, hi


def cohens_d(delta: Iterable[float]) -> float:
    arr = np.asarray(list(delta), dtype=float)
    if arr.size < 2:
        return 0.0
    std = float(np.std(arr, ddof=1))
    if std == 0.0:
        return 0.0
    return float(np.mean(arr) / std)


def rank_correlation(x: Iterable[float], y: Iterable[float]) -> float:
    x_arr = pd.Series(list(x), dtype=float).rank(method="average").to_numpy()
    y_arr = pd.Series(list(y), dtype=float).rank(method="average").to_numpy()
    if x_arr.size < 2 or np.std(x_arr) == 0.0 or np.std(y_arr) == 0.0:
        return 0.0
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def paired_selector_summary(
    seed_df: pd.DataFrame,
    baseline: str,
    treatments: list[str],
    metric: str,
    group_filter: dict[str, object] | None = None,
) -> pd.DataFrame:
    df = seed_df.copy()
    if group_filter:
        for key, value in group_filter.items():
            df = df[df[key] == value]

    keys = ["suite", "graph_family", "hidden_failure", "stress_level", "scenario", "N", "seed"]
    base = df[df["selector"] == baseline][keys + [metric]].rename(columns={metric: "baseline_value"})
    rows: list[dict[str, float | int | str]] = []
    for treatment in treatments:
        other = df[df["selector"] == treatment][keys + [metric]].rename(columns={metric: "treatment_value"})
        joined = base.merge(other, on=keys, how="inner")
        if joined.empty:
            continue
        joined["delta"] = joined["treatment_value"] - joined["baseline_value"]
        lo, hi = bootstrap_ci(joined["delta"], seed=len(treatment) + len(metric))
        rows.append(
            {
                "baseline": baseline,
                "treatment": treatment,
                "metric": metric,
                "n_pairs": int(joined.shape[0]),
                "mean_delta": float(joined["delta"].mean()),
                "ci95_low": lo,
                "ci95_high": hi,
                "cohens_d": cohens_d(joined["delta"]),
                "fraction_improved": float(np.mean(joined["delta"] > 0.0)),
            }
        )
    return pd.DataFrame(rows)
