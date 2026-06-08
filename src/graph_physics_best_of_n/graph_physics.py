"""Controlled graph-physics candidate generator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


Edge = tuple[int, int]


@dataclass(frozen=True)
class GraphWorld:
    positions: np.ndarray
    velocities: np.ndarray
    targets: np.ndarray
    observed_edges: tuple[Edge, ...]
    hidden_edges: tuple[Edge, ...]
    observed_rest_lengths: np.ndarray
    hidden_rest_lengths: np.ndarray


@dataclass(frozen=True)
class Candidate:
    scenario: str
    score: float
    real_utility: float
    imagined_target_error: float
    true_target_error: float
    observed_energy: float
    hidden_energy: float
    edge_violation: float
    action_norm: float
    diagnostics: dict[str, float | str]


SCENARIOS = ["aligned", "edge_shortcut", "hidden_constraint", "long_horizon", "raw"]


def _edge_lengths(positions: np.ndarray, edges: tuple[Edge, ...]) -> np.ndarray:
    if not edges:
        return np.zeros(0, dtype=float)
    return np.asarray([np.linalg.norm(positions[i] - positions[j]) for i, j in edges], dtype=float)


def make_world(seed: int, scenario: str = "raw", n_nodes: int = 6) -> GraphWorld:
    """Create a small mass-spring graph with observed and hidden constraints."""

    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    rng = np.random.default_rng(seed)
    angles = np.linspace(0.0, 2.0 * np.pi, n_nodes, endpoint=False)
    radius = 1.0 + 0.08 * rng.normal(size=n_nodes)
    positions = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])
    positions += 0.04 * rng.normal(size=positions.shape)
    velocities = 0.02 * rng.normal(size=positions.shape)

    targets = positions.copy()
    shift = np.array([0.95, -0.3]) if scenario != "aligned" else np.array([0.35, -0.15])
    targets[0] += shift
    targets[1] += 0.45 * shift
    if scenario in {"long_horizon", "raw"}:
        targets[3] -= np.array([0.35, 0.45])

    observed_edges: tuple[Edge, ...] = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3))
    hidden_edges: tuple[Edge, ...] = () if scenario == "aligned" else ((0, 4), (1, 5))
    observed_rest = _edge_lengths(positions, observed_edges)
    hidden_rest = _edge_lengths(positions, hidden_edges)
    if scenario in {"hidden_constraint", "raw"} and hidden_rest.size:
        hidden_rest = hidden_rest * 0.72
    elif scenario == "edge_shortcut" and hidden_rest.size:
        hidden_rest = hidden_rest * 0.84
    return GraphWorld(positions, velocities, targets, observed_edges, hidden_edges, observed_rest, hidden_rest)


def spring_energy(positions: np.ndarray, edges: tuple[Edge, ...], rest_lengths: np.ndarray) -> float:
    lengths = _edge_lengths(positions, edges)
    if lengths.size == 0:
        return 0.0
    stretch = lengths - rest_lengths
    return float(np.mean(stretch * stretch))


def rollout(
    world: GraphWorld,
    actions: np.ndarray,
    include_hidden: bool,
    horizon_scale: float = 1.0,
) -> tuple[np.ndarray, float, float]:
    """Roll out a damped spring graph and return positions plus energies."""

    pos = np.array(world.positions, dtype=float, copy=True)
    vel = np.array(world.velocities, dtype=float, copy=True)
    dt = 0.12 * horizon_scale
    damping = 0.12 if include_hidden else 0.07
    stiffness = 0.42 if include_hidden else 0.26

    for action in actions:
        forces = np.array(action, dtype=float, copy=True) - damping * vel
        edge_sets = [(world.observed_edges, world.observed_rest_lengths)]
        if include_hidden:
            edge_sets.append((world.hidden_edges, world.hidden_rest_lengths))
        for edges, rest_lengths in edge_sets:
            for edge_index, (i, j) in enumerate(edges):
                delta = pos[j] - pos[i]
                dist = float(np.linalg.norm(delta)) + 1e-9
                direction = delta / dist
                stretch = dist - float(rest_lengths[edge_index])
                spring_force = stiffness * stretch * direction
                forces[i] += spring_force
                forces[j] -= spring_force
        forces = np.clip(forces, -3.0, 3.0)
        vel = 0.98 * vel + dt * forces
        pos = pos + dt * vel

    observed_energy = spring_energy(pos, world.observed_edges, world.observed_rest_lengths)
    hidden_energy = spring_energy(pos, world.hidden_edges, world.hidden_rest_lengths)
    return pos, observed_energy, hidden_energy


def _sample_actions(world: GraphWorld, rng: np.random.Generator, scenario: str, steps: int) -> np.ndarray:
    to_target = world.targets - world.positions
    base = np.repeat(to_target[None, :, :], steps, axis=0)
    if scenario == "aligned":
        gain = rng.uniform(0.45, 0.9)
        shortcut = 0.15
    elif scenario == "long_horizon":
        gain = rng.lognormal(mean=0.0, sigma=0.55)
        shortcut = rng.gamma(shape=1.8, scale=0.55)
    else:
        gain = rng.lognormal(mean=0.2, sigma=0.7)
        shortcut = rng.gamma(shape=2.0, scale=0.65)

    actions = gain * base / max(1, steps)
    noise = rng.normal(scale=0.11 + 0.05 * shortcut, size=actions.shape)
    actions += noise
    if scenario in {"edge_shortcut", "hidden_constraint", "raw"}:
        direction = world.targets[0] - world.positions[0]
        direction = direction / (np.linalg.norm(direction) + 1e-9)
        actions[:, 0, :] += shortcut * direction
        actions[:, 4, :] -= 0.42 * shortcut * direction
    return actions


def make_candidate(world: GraphWorld, scenario: str, seed: int, steps: int = 14) -> Candidate:
    rng = np.random.default_rng(seed)
    actions = _sample_actions(world, rng, scenario, steps)
    horizon_scale = 1.25 if scenario == "long_horizon" else 1.0
    imagined_pos, imagined_observed_energy, _ = rollout(world, actions, include_hidden=False, horizon_scale=horizon_scale)
    true_pos, true_observed_energy, hidden_energy = rollout(world, actions, include_hidden=True, horizon_scale=horizon_scale)

    imagined_target_error = float(np.mean(np.linalg.norm(imagined_pos - world.targets, axis=1)))
    true_target_error = float(np.mean(np.linalg.norm(true_pos - world.targets, axis=1)))
    action_norm = float(np.mean(np.linalg.norm(actions, axis=2)))
    edge_violation = float(true_observed_energy + hidden_energy)

    shortcut_bonus = 0.24 * np.tanh(action_norm)
    if scenario == "aligned":
        shortcut_bonus = 0.04 * np.tanh(action_norm)
    score = -imagined_target_error - 0.06 * imagined_observed_energy + shortcut_bonus
    real_utility = -true_target_error - 0.55 * hidden_energy - 0.16 * true_observed_energy - 0.045 * action_norm
    diagnostics = {
        "selector_score_label": "unselected",
        "imagined_observed_energy": float(imagined_observed_energy),
        "true_observed_energy": float(true_observed_energy),
        "hidden_energy": float(hidden_energy),
        "action_norm": action_norm,
    }
    return Candidate(
        scenario=scenario,
        score=float(score),
        real_utility=float(real_utility),
        imagined_target_error=imagined_target_error,
        true_target_error=true_target_error,
        observed_energy=float(true_observed_energy),
        hidden_energy=float(hidden_energy),
        edge_violation=edge_violation,
        action_norm=action_norm,
        diagnostics=diagnostics,
    )


def generate_candidates(world: GraphWorld, n: int, scenario: str, seed: int) -> list[Candidate]:
    if n < 1:
        raise ValueError("n must be at least 1")
    return [make_candidate(world, scenario, seed + 104_729 * i) for i in range(n)]

