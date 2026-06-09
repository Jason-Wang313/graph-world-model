from graph_physics_best_of_n.graph_physics import GRAPH_FAMILIES, HIDDEN_FAILURES, STRESS_LEVELS, generate_candidates, make_world
from graph_physics_best_of_n.selection import SELECTORS, adaptive_gate_decision, combined_repair_score
from graph_physics_best_of_n.theory import exact_best_of_n_expected_utility


def test_raw_high_n_exposes_selected_tail_risk():
    world = make_world(123, scenario="raw")
    pool = generate_candidates(world, 128, scenario="raw", seed=99)
    utilities = [candidate.real_utility for candidate in pool]
    scores = [candidate.score for candidate in pool]
    raw_high_n = exact_best_of_n_expected_utility(utilities, scores, n=64)
    oracle_high_n = exact_best_of_n_expected_utility(utilities, utilities, n=64)
    best_score_candidate = max(pool, key=lambda candidate: candidate.score)
    best_utility_candidate = max(pool, key=lambda candidate: candidate.real_utility)
    assert oracle_high_n >= raw_high_n
    assert best_score_candidate.real_utility < best_utility_candidate.real_utility
    assert best_score_candidate.hidden_energy > best_utility_candidate.hidden_energy


def test_combined_repair_selects_less_risky_candidate_than_raw():
    world = make_world(321, scenario="hidden_constraint")
    candidates = generate_candidates(world, 64, scenario="hidden_constraint", seed=7)
    raw = SELECTORS["raw"](candidates, seed=0)
    repaired = SELECTORS["combined_repair"](candidates, seed=0)
    assert repaired.real_utility >= raw.real_utility or repaired.edge_violation <= raw.edge_violation
    assert repaired.diagnostics["selector_score"] >= combined_repair_score(raw)


def test_graph_stress_axes_generate_finite_candidates():
    for graph_family in GRAPH_FAMILIES:
        world = make_world(
            17,
            scenario="raw",
            graph_family=graph_family,
            hidden_failure=HIDDEN_FAILURES[0],
            stress_level=STRESS_LEVELS[-1],
        )
        candidates = generate_candidates(world, 4, seed=23)
        assert len(candidates) == 4
        assert all(candidate.graph_family == graph_family for candidate in candidates)
        assert all(candidate.real_utility < 1.0 for candidate in candidates)


def test_adaptive_gate_reports_decision():
    world = make_world(991, scenario="raw", hidden_failure="long_horizon_drift", stress_level="severe")
    candidates = generate_candidates(world, 32, seed=3)
    decision = adaptive_gate_decision(candidates, n=32, seed=0)
    selected = SELECTORS["adaptive_gate"](candidates, seed=0)
    assert decision["decision"] in {"allow_raw", "block_raw_use_repair"}
    assert selected.diagnostics["selector_score_label"] == "adaptive_gate"
