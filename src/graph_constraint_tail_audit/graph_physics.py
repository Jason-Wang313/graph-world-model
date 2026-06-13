"""Controlled graph-physics candidate generator.

The simulator is intentionally small enough for CPU-only audit runs, but it
covers several graph topologies and hidden failure modes. The imagined model
sees only an imperfect graph; the real evaluator rolls out the true graph.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


Edge = tuple[int, int]

GRAPH_FAMILIES = ["ring_chord", "chain", "grid", "random_geometric", "clustered"]
HIDDEN_FAILURES = ["omitted_edges", "shifted_rest_lengths", "delayed_damping", "topology_aliasing", "long_horizon_drift"]
STRESS_LEVELS = ["mild", "medium", "severe"]
SCENARIOS = ["aligned", "edge_shortcut", "hidden_constraint", "long_horizon", "raw"]
SCENARIO_BY_FAILURE = {
    "omitted_edges": "raw",
    "shifted_rest_lengths": "hidden_constraint",
    "delayed_damping": "long_horizon",
    "topology_aliasing": "edge_shortcut",
    "long_horizon_drift": "long_horizon",
}

_STRESS_SCALE = {"mild": 0.55, "medium": 0.9, "severe": 1.25}


@dataclass(frozen=True)
class GraphWorld:
    graph_family: str
    hidden_failure: str
    stress_level: str
    scenario: str
    positions: np.ndarray
    velocities: np.ndarray
    targets: np.ndarray
    imagined_edges: tuple[Edge, ...]
    true_observed_edges: tuple[Edge, ...]
    hidden_edges: tuple[Edge, ...]
    imagined_rest_lengths: np.ndarray
    true_observed_rest_lengths: np.ndarray
    hidden_rest_lengths: np.ndarray
    imagined_damping: float
    true_damping: float
    imagined_stiffness: float
    true_stiffness: float
    horizon_scale: float


@dataclass(frozen=True)
class Candidate:
    scenario: str
    graph_family: str
    hidden_failure: str
    stress_level: str
    score: float
    real_utility: float
    imagined_target_error: float
    true_target_error: float
    observed_energy: float
    hidden_energy: float
    edge_violation: float
    action_norm: float
    calibration_gap: float
    diagnostics: dict[str, float | str]


def _unique_edges(edges: list[Edge]) -> tuple[Edge, ...]:
    normalized = {tuple(sorted((int(i), int(j)))) for i, j in edges if int(i) != int(j)}
    return tuple(sorted(normalized))


def _edge_lengths(positions: np.ndarray, edges: tuple[Edge, ...]) -> np.ndarray:
    if not edges:
        return np.zeros(0, dtype=float)
    return np.asarray([np.linalg.norm(positions[i] - positions[j]) for i, j in edges], dtype=float)


def _ring_layout(rng: np.random.Generator, n: int) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    radius = 1.0 + 0.08 * rng.normal(size=n)
    positions = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])
    return positions + 0.035 * rng.normal(size=(n, 2))


def _family_layout(graph_family: str, rng: np.random.Generator, n_nodes: int | None) -> tuple[np.ndarray, tuple[Edge, ...]]:
    if graph_family not in GRAPH_FAMILIES:
        raise ValueError(f"unknown graph_family {graph_family!r}")

    if graph_family == "ring_chord":
        n = n_nodes or 6
        positions = _ring_layout(rng, n)
        edges = [(i, (i + 1) % n) for i in range(n)] + [(0, n // 2), (1, (n // 2 + 1) % n)]
        return positions, _unique_edges(edges)

    if graph_family == "chain":
        n = n_nodes or 7
        x = np.linspace(-1.25, 1.25, n)
        positions = np.column_stack([x, 0.12 * rng.normal(size=n)])
        positions += 0.025 * rng.normal(size=(n, 2))
        return positions, _unique_edges([(i, i + 1) for i in range(n - 1)])

    if graph_family == "grid":
        side = 3
        coords = [(x, y) for y in range(side) for x in range(side)]
        positions = np.asarray(coords, dtype=float)
        positions = (positions - np.mean(positions, axis=0)) / 1.35
        positions += 0.035 * rng.normal(size=positions.shape)
        edges: list[Edge] = []
        for y in range(side):
            for x in range(side):
                idx = y * side + x
                if x + 1 < side:
                    edges.append((idx, y * side + x + 1))
                if y + 1 < side:
                    edges.append((idx, (y + 1) * side + x))
        return positions, _unique_edges(edges)

    if graph_family == "random_geometric":
        n = n_nodes or 8
        positions = rng.uniform(-1.1, 1.1, size=(n, 2))
        order = np.argsort(positions[:, 0])
        edges = [(int(order[i]), int(order[i + 1])) for i in range(n - 1)]
        for i in range(n):
            distances = np.linalg.norm(positions - positions[i], axis=1)
            for j in np.argsort(distances)[1:3]:
                if distances[j] < 1.05:
                    edges.append((i, int(j)))
        return positions, _unique_edges(edges)

    n = n_nodes or 8
    left = rng.normal(loc=(-0.75, 0.0), scale=0.16, size=(n // 2, 2))
    right = rng.normal(loc=(0.75, 0.0), scale=0.16, size=(n - n // 2, 2))
    positions = np.vstack([left, right])
    split = n // 2
    edges = []
    for start, end in [(0, split), (split, n)]:
        for i in range(start, end):
            for j in range(i + 1, end):
                edges.append((i, j))
    edges.extend([(split - 1, split), (0, n - 1)])
    return positions, _unique_edges(edges)


def _candidate_hidden_edges(n_nodes: int, observed_edges: tuple[Edge, ...], rng: np.random.Generator) -> tuple[Edge, ...]:
    observed = set(observed_edges)
    candidates = [tuple(sorted((i, j))) for i in range(n_nodes) for j in range(i + 1, n_nodes) if (i, j) not in observed]
    if not candidates:
        return ()
    rng.shuffle(candidates)
    return _unique_edges(candidates[: max(2, min(4, n_nodes // 2))])


def _aliased_edges(n_nodes: int, observed_edges: tuple[Edge, ...], rng: np.random.Generator) -> tuple[Edge, ...]:
    hidden_candidates = list(_candidate_hidden_edges(n_nodes, observed_edges, rng))
    if not hidden_candidates or len(observed_edges) < 2:
        return observed_edges
    aliased = list(observed_edges[:-1]) + [hidden_candidates[0]]
    return _unique_edges(aliased)


def make_world(
    seed: int,
    scenario: str = "raw",
    n_nodes: int | None = None,
    graph_family: str = "ring_chord",
    hidden_failure: str = "omitted_edges",
    stress_level: str = "medium",
) -> GraphWorld:
    """Create a mass-spring graph with an imperfect imagined graph."""

    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    if hidden_failure not in HIDDEN_FAILURES:
        raise ValueError(f"unknown hidden_failure {hidden_failure!r}")
    if stress_level not in STRESS_LEVELS:
        raise ValueError(f"unknown stress_level {stress_level!r}")

    rng = np.random.default_rng(seed)
    stress = _STRESS_SCALE[stress_level]
    positions, observed_edges = _family_layout(graph_family, rng, n_nodes)
    velocities = (0.018 + 0.012 * stress) * rng.normal(size=positions.shape)
    n = positions.shape[0]

    targets = positions.copy()
    focus = 0
    partner = min(1, n - 1)
    far = int(np.argmax(np.linalg.norm(positions - positions[focus], axis=1)))
    shift_mag = 0.28 if scenario == "aligned" else 0.62 + 0.22 * stress
    direction = np.asarray([1.0, -0.35])
    direction = direction / np.linalg.norm(direction)
    targets[focus] += shift_mag * direction
    targets[partner] += 0.35 * shift_mag * direction
    if scenario in {"long_horizon", "raw"}:
        targets[far] -= (0.28 + 0.16 * stress) * np.asarray([0.35, 1.0])
    if scenario == "edge_shortcut":
        targets[far] += 0.25 * shift_mag * np.asarray([-direction[1], direction[0]])

    hidden_edges = _candidate_hidden_edges(n, observed_edges, rng)
    imagined_edges = observed_edges
    true_observed_edges = observed_edges
    imagined_rest = _edge_lengths(positions, imagined_edges)
    true_observed_rest = _edge_lengths(positions, true_observed_edges)
    hidden_rest = _edge_lengths(positions, hidden_edges)

    imagined_damping = 0.07
    true_damping = 0.12
    imagined_stiffness = 0.26
    true_stiffness = 0.42
    horizon_scale = 1.0

    if hidden_failure == "shifted_rest_lengths":
        hidden_rest = hidden_rest * (1.0 - 0.16 * stress)
        true_observed_rest = true_observed_rest * (1.0 + 0.03 * stress)
    elif hidden_failure == "delayed_damping":
        true_damping = 0.17 + 0.05 * stress
        horizon_scale = 1.12 + 0.08 * stress
    elif hidden_failure == "topology_aliasing":
        imagined_edges = _aliased_edges(n, observed_edges, rng)
        imagined_rest = _edge_lengths(positions, imagined_edges) * (1.0 + 0.04 * stress)
        hidden_rest = hidden_rest * (1.0 - 0.10 * stress)
    elif hidden_failure == "long_horizon_drift":
        horizon_scale = 1.20 + 0.18 * stress
        true_stiffness = 0.48 + 0.08 * stress
        hidden_rest = hidden_rest * (1.0 - 0.08 * stress)
    elif hidden_failure == "omitted_edges":
        hidden_rest = hidden_rest * (1.0 - 0.12 * stress)

    if scenario == "aligned":
        hidden_edges = ()
        hidden_rest = np.zeros(0, dtype=float)
        true_damping = imagined_damping + 0.03
        true_stiffness = imagined_stiffness + 0.08
        horizon_scale = 1.0

    return GraphWorld(
        graph_family=graph_family,
        hidden_failure=hidden_failure,
        stress_level=stress_level,
        scenario=scenario,
        positions=positions,
        velocities=velocities,
        targets=targets,
        imagined_edges=imagined_edges,
        true_observed_edges=true_observed_edges,
        hidden_edges=hidden_edges,
        imagined_rest_lengths=imagined_rest,
        true_observed_rest_lengths=true_observed_rest,
        hidden_rest_lengths=hidden_rest,
        imagined_damping=imagined_damping,
        true_damping=true_damping,
        imagined_stiffness=imagined_stiffness,
        true_stiffness=true_stiffness,
        horizon_scale=horizon_scale,
    )


def spring_energy(positions: np.ndarray, edges: tuple[Edge, ...], rest_lengths: np.ndarray) -> float:
    lengths = _edge_lengths(positions, edges)
    if lengths.size == 0:
        return 0.0
    stretch = lengths - rest_lengths
    return float(np.mean(stretch * stretch))


def rollout(world: GraphWorld, actions: np.ndarray, include_hidden: bool) -> tuple[np.ndarray, float, float]:
    """Roll out the imagined or true damped spring graph."""

    pos = np.array(world.positions, dtype=float, copy=True)
    vel = np.array(world.velocities, dtype=float, copy=True)
    dt = 0.12 * world.horizon_scale
    damping = world.true_damping if include_hidden else world.imagined_damping
    stiffness = world.true_stiffness if include_hidden else world.imagined_stiffness

    if include_hidden:
        edge_sets = [(world.true_observed_edges, world.true_observed_rest_lengths), (world.hidden_edges, world.hidden_rest_lengths)]
    else:
        edge_sets = [(world.imagined_edges, world.imagined_rest_lengths)]

    for action in actions:
        forces = np.array(action, dtype=float, copy=True) - damping * vel
        for edges, rest_lengths in edge_sets:
            for edge_index, (i, j) in enumerate(edges):
                delta = pos[j] - pos[i]
                dist = float(np.linalg.norm(delta)) + 1e-9
                direction = delta / dist
                stretch = dist - float(rest_lengths[edge_index])
                spring_force = stiffness * stretch * direction
                forces[i] += spring_force
                forces[j] -= spring_force
        forces = np.clip(forces, -3.5, 3.5)
        vel = 0.98 * vel + dt * forces
        pos = pos + dt * vel

    observed_energy = spring_energy(pos, world.true_observed_edges, world.true_observed_rest_lengths)
    hidden_energy = spring_energy(pos, world.hidden_edges, world.hidden_rest_lengths)
    return pos, observed_energy, hidden_energy


def _sample_actions(world: GraphWorld, rng: np.random.Generator, steps: int) -> np.ndarray:
    stress = _STRESS_SCALE[world.stress_level]
    to_target = world.targets - world.positions
    base = np.repeat(to_target[None, :, :], steps, axis=0)
    if world.scenario == "aligned":
        gain = rng.uniform(0.38, 0.78)
        shortcut = 0.08 * stress
    elif world.scenario == "long_horizon":
        gain = rng.lognormal(mean=0.0, sigma=0.46 + 0.08 * stress)
        shortcut = rng.gamma(shape=1.5, scale=0.40 * stress)
    else:
        gain = rng.lognormal(mean=0.16, sigma=0.58 + 0.10 * stress)
        shortcut = rng.gamma(shape=1.8, scale=0.45 * stress)

    actions = gain * base / max(1, steps)
    actions += rng.normal(scale=0.08 + 0.035 * stress + 0.035 * shortcut, size=actions.shape)

    if world.scenario in {"edge_shortcut", "hidden_constraint", "raw"}:
        focus = 0
        far = int(np.argmax(np.linalg.norm(world.positions - world.positions[focus], axis=1)))
        direction = world.targets[focus] - world.positions[focus]
        direction = direction / (np.linalg.norm(direction) + 1e-9)
        actions[:, focus, :] += shortcut * direction
        actions[:, far, :] -= 0.38 * shortcut * direction
    if world.hidden_failure in {"delayed_damping", "long_horizon_drift"}:
        actions += 0.05 * stress * np.cumsum(actions, axis=0) / steps
    return actions


def make_candidate(world: GraphWorld, seed: int, steps: int = 14) -> Candidate:
    rng = np.random.default_rng(seed)
    actions = _sample_actions(world, rng, steps)
    imagined_pos, imagined_observed_energy, _ = rollout(world, actions, include_hidden=False)
    true_pos, true_observed_energy, hidden_energy = rollout(world, actions, include_hidden=True)

    imagined_target_error = float(np.mean(np.linalg.norm(imagined_pos - world.targets, axis=1)))
    true_target_error = float(np.mean(np.linalg.norm(true_pos - world.targets, axis=1)))
    action_norm = float(np.mean(np.linalg.norm(actions, axis=2)))
    edge_violation = float(true_observed_energy + hidden_energy)
    calibration_gap = float(true_target_error - imagined_target_error)

    stress = _STRESS_SCALE[world.stress_level]
    shortcut_bonus = (0.11 + 0.09 * stress) * np.tanh(action_norm)
    if world.scenario == "aligned":
        shortcut_bonus = 0.03 * np.tanh(action_norm)
    score = -imagined_target_error - 0.055 * imagined_observed_energy + shortcut_bonus
    real_utility = (
        -true_target_error
        - (0.48 + 0.11 * stress) * hidden_energy
        - 0.15 * true_observed_energy
        - 0.040 * action_norm
        - 0.09 * max(0.0, calibration_gap)
    )
    diagnostics = {
        "selector_score_label": "unselected",
        "imagined_observed_energy": float(imagined_observed_energy),
        "true_observed_energy": float(true_observed_energy),
        "hidden_energy": float(hidden_energy),
        "action_norm": action_norm,
        "calibration_gap": calibration_gap,
    }
    return Candidate(
        scenario=world.scenario,
        graph_family=world.graph_family,
        hidden_failure=world.hidden_failure,
        stress_level=world.stress_level,
        score=float(score),
        real_utility=float(real_utility),
        imagined_target_error=imagined_target_error,
        true_target_error=true_target_error,
        observed_energy=float(true_observed_energy),
        hidden_energy=float(hidden_energy),
        edge_violation=edge_violation,
        action_norm=action_norm,
        calibration_gap=calibration_gap,
        diagnostics=diagnostics,
    )


def generate_candidates(world: GraphWorld, n: int, scenario: str | None = None, seed: int = 0) -> list[Candidate]:
    """Generate deterministic candidates. The scenario argument is accepted for backwards compatibility."""

    if n < 1:
        raise ValueError("n must be at least 1")
    if scenario is not None and scenario != world.scenario:
        raise ValueError("scenario must match the world scenario")
    return [make_candidate(world, seed + 104_729 * i) for i in range(n)]
