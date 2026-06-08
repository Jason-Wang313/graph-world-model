"""Selectors and lightweight graph-physics repair scores."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

import numpy as np

from .graph_physics import Candidate


def _select_max(candidates: list[Candidate], key: Callable[[Candidate], float], seed: int, label: str) -> Candidate:
    if not candidates:
        raise ValueError("candidates must be non-empty")
    scores = np.asarray([key(candidate) for candidate in candidates], dtype=float)
    max_score = float(np.max(scores))
    tied = np.flatnonzero(np.isclose(scores, max_score))
    rng = np.random.default_rng(seed)
    chosen = candidates[int(rng.choice(tied))]
    diagnostics = dict(chosen.diagnostics)
    diagnostics["selector_score_label"] = label
    diagnostics["selector_score"] = max_score
    return replace(chosen, score=max_score, diagnostics=diagnostics)


def graph_energy_calibrated_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.40 * candidate.observed_energy - 0.05 * candidate.action_norm)


def constraint_probe_score(candidate: Candidate) -> float:
    proxy_hidden_risk = candidate.action_norm * (0.35 + 0.65 * candidate.hidden_energy / (1.0 + candidate.hidden_energy))
    return float(candidate.score - 0.22 * proxy_hidden_risk - 0.20 * candidate.edge_violation)


def combined_repair_score(candidate: Candidate) -> float:
    return float(
        candidate.score
        - 0.38 * candidate.edge_violation
        - 0.12 * candidate.action_norm
        - 0.22 * max(0.0, candidate.true_target_error - candidate.imagined_target_error)
    )


def select_raw(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, lambda candidate: candidate.score, seed=seed, label="raw")


def select_graph_energy_calibrated(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, graph_energy_calibrated_score, seed=seed, label="graph_energy_calibrated")


def select_constraint_probe(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, constraint_probe_score, seed=seed, label="constraint_probe")


def select_combined_repair(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, combined_repair_score, seed=seed, label="combined_repair")


def select_random(candidates: list[Candidate], seed: int = 0) -> Candidate:
    if not candidates:
        raise ValueError("candidates must be non-empty")
    rng = np.random.default_rng(seed)
    chosen = candidates[int(rng.integers(0, len(candidates)))]
    diagnostics = dict(chosen.diagnostics)
    diagnostics["selector_score_label"] = "random"
    diagnostics["selector_score"] = chosen.score
    return replace(chosen, diagnostics=diagnostics)


def select_oracle(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, lambda candidate: candidate.real_utility, seed=seed, label="oracle")


SELECTORS: dict[str, Callable[[list[Candidate], int], Candidate]] = {
    "raw": select_raw,
    "graph_energy_calibrated": select_graph_energy_calibrated,
    "constraint_probe": select_constraint_probe,
    "combined_repair": select_combined_repair,
    "random": select_random,
    "oracle": select_oracle,
}

