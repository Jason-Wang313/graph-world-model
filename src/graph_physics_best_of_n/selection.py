"""Selectors, repair scores, ablations, and adaptive-N gating."""

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


def hidden_risk_proxy(candidate: Candidate) -> float:
    return float(candidate.edge_violation + 0.30 * candidate.action_norm + 0.35 * max(0.0, candidate.calibration_gap))


def observed_energy_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.52 * candidate.observed_energy)


def action_penalty_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.16 * candidate.action_norm)


def graph_energy_calibrated_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.34 * candidate.observed_energy - 0.08 * candidate.action_norm)


def constraint_probe_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.30 * hidden_risk_proxy(candidate))


def calibration_gap_score(candidate: Candidate) -> float:
    return float(candidate.score - 0.32 * max(0.0, candidate.calibration_gap))


def combined_repair_score(candidate: Candidate) -> float:
    return float(
        candidate.score
        - 0.36 * candidate.edge_violation
        - 0.11 * candidate.action_norm
        - 0.24 * max(0.0, candidate.calibration_gap)
        - 0.10 * candidate.observed_energy
    )


def select_raw(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, lambda candidate: candidate.score, seed=seed, label="raw")


def select_observed_energy_ablation(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, observed_energy_score, seed=seed, label="observed_energy_ablation")


def select_action_penalty_ablation(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, action_penalty_score, seed=seed, label="action_penalty_ablation")


def select_calibration_gap_ablation(candidates: list[Candidate], seed: int = 0) -> Candidate:
    return _select_max(candidates, calibration_gap_score, seed=seed, label="calibration_gap_ablation")


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


def adaptive_gate_decision(candidates: list[Candidate], n: int | None = None, seed: int = 0) -> dict[str, float | str | bool]:
    """Pilot-label style gate for whether raw high-N selection is admitted."""

    if not candidates:
        raise ValueError("candidates must be non-empty")
    n = len(candidates) if n is None else int(n)
    raw = select_raw(candidates, seed=seed)
    repaired = select_combined_repair(candidates, seed=seed)
    risk_values = np.asarray([hidden_risk_proxy(candidate) for candidate in candidates], dtype=float)
    raw_risk = hidden_risk_proxy(raw)
    risk_threshold = float(np.quantile(risk_values, 0.60) + 0.08)
    repair_gain = float(repaired.real_utility - raw.real_utility)
    should_repair = bool(n >= 8 and (raw_risk > risk_threshold or repair_gain > 1e-9))
    return {
        "decision": "block_raw_use_repair" if should_repair else "allow_raw",
        "blocked_raw": should_repair,
        "raw_risk": float(raw_risk),
        "risk_threshold": risk_threshold,
        "repair_gain": repair_gain,
        "selected_label": "combined_repair" if should_repair else "raw",
    }


def select_adaptive_gate(candidates: list[Candidate], seed: int = 0) -> Candidate:
    decision = adaptive_gate_decision(candidates, seed=seed)
    selected = select_combined_repair(candidates, seed=seed) if decision["blocked_raw"] else select_raw(candidates, seed=seed)
    diagnostics = dict(selected.diagnostics)
    diagnostics.update(decision)
    diagnostics["selector_score_label"] = "adaptive_gate"
    return replace(selected, diagnostics=diagnostics)


SELECTORS: dict[str, Callable[[list[Candidate], int], Candidate]] = {
    "raw": select_raw,
    "observed_energy_ablation": select_observed_energy_ablation,
    "action_penalty_ablation": select_action_penalty_ablation,
    "calibration_gap_ablation": select_calibration_gap_ablation,
    "graph_energy_calibrated": select_graph_energy_calibrated,
    "constraint_probe": select_constraint_probe,
    "combined_repair": select_combined_repair,
    "adaptive_gate": select_adaptive_gate,
    "random": select_random,
    "oracle": select_oracle,
}
