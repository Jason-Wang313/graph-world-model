from graph_physics_best_of_n.graph_physics import generate_candidates, make_world
from graph_physics_best_of_n.selection import SELECTORS, combined_repair_score
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
    assert oracle_high_n >= raw_high_n + 0.03
    assert best_score_candidate.real_utility < best_utility_candidate.real_utility
    assert best_score_candidate.hidden_energy > best_utility_candidate.hidden_energy


def test_combined_repair_selects_less_risky_candidate_than_raw():
    world = make_world(321, scenario="hidden_constraint")
    candidates = generate_candidates(world, 64, scenario="hidden_constraint", seed=7)
    raw = SELECTORS["raw"](candidates, seed=0)
    repaired = SELECTORS["combined_repair"](candidates, seed=0)
    assert repaired.real_utility >= raw.real_utility
    assert repaired.diagnostics["selector_score"] >= combined_repair_score(raw)
