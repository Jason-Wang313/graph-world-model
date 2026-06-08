"""Finite tie-aware Best-of-N selection laws."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class TieGroup:
    """One score-equivalence class in descending score order."""

    score: float
    indices: tuple[int, ...]
    probability: float
    mean_utility: float


def _as_1d_float(values: Iterable[float], name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite")
    return arr


def score_tie_groups(scores: Iterable[float]) -> list[tuple[float, np.ndarray]]:
    score_arr = _as_1d_float(scores, "scores")
    return [(float(score), np.flatnonzero(score_arr == score)) for score in np.unique(score_arr)[::-1]]


def selected_tie_groups(
    utilities: Iterable[float],
    scores: Iterable[float] | None = None,
    n: int = 1,
) -> list[TieGroup]:
    """Exact selected-group probabilities for N i.i.d. finite draws."""

    if n < 1:
        raise ValueError("n must be at least 1")
    utility_arr = _as_1d_float(utilities, "utilities")
    score_arr = utility_arr if scores is None else _as_1d_float(scores, "scores")
    if utility_arr.shape != score_arr.shape:
        raise ValueError("utilities and scores must have the same length")

    m = utility_arr.size
    groups: list[TieGroup] = []
    above = 0
    for score, idx in score_tie_groups(score_arr):
        group_size = int(idx.size)
        below = m - above - group_size
        probability = ((group_size + below) / m) ** n - (below / m) ** n
        groups.append(
            TieGroup(
                score=score,
                indices=tuple(int(i) for i in idx),
                probability=float(probability),
                mean_utility=float(np.mean(utility_arr[idx])),
            )
        )
        above += group_size
    return groups


def exact_best_of_n_expected_utility(
    utilities: Iterable[float],
    scores: Iterable[float] | None = None,
    n: int = 1,
) -> float:
    groups = selected_tie_groups(utilities, scores=scores, n=n)
    return float(sum(group.probability * group.mean_utility for group in groups))


def expected_curve(
    utilities: Iterable[float],
    scores: Iterable[float] | None,
    ns: Iterable[int],
) -> dict[int, float]:
    return {int(n): exact_best_of_n_expected_utility(utilities, scores, int(n)) for n in ns}


def monte_carlo_best_of_n(
    utilities: Iterable[float],
    scores: Iterable[float] | None = None,
    n: int = 1,
    trials: int = 10_000,
    seed: int = 0,
) -> float:
    """Monte Carlo estimator matching the tie-aware finite law."""

    if trials < 1:
        raise ValueError("trials must be positive")
    if n < 1:
        raise ValueError("n must be at least 1")
    utility_arr = _as_1d_float(utilities, "utilities")
    score_arr = utility_arr if scores is None else _as_1d_float(scores, "scores")
    if utility_arr.shape != score_arr.shape:
        raise ValueError("utilities and scores must have the same length")

    rng = np.random.default_rng(seed)
    selected = np.empty(trials, dtype=float)
    for trial in range(trials):
        sample = rng.integers(0, utility_arr.size, size=n)
        sampled_scores = score_arr[sample]
        max_score = np.max(sampled_scores)
        tied_positions = np.flatnonzero(sampled_scores == max_score)
        chosen_position = int(rng.choice(tied_positions))
        selected[trial] = utility_arr[sample[chosen_position]]
    return float(np.mean(selected))


def law_validation_row(
    utilities: Iterable[float],
    scores: Iterable[float],
    n: int,
    trials: int,
    seed: int,
) -> dict[str, float | int]:
    predicted = exact_best_of_n_expected_utility(utilities, scores, n=n)
    empirical = monte_carlo_best_of_n(utilities, scores, n=n, trials=trials, seed=seed)
    return {
        "N": int(n),
        "predicted_selected_utility": float(predicted),
        "empirical_selected_utility": float(empirical),
        "absolute_error": float(abs(predicted - empirical)),
        "trials": int(trials),
        "seed": int(seed),
    }

