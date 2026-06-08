import math

from graph_physics_best_of_n.theory import exact_best_of_n_expected_utility, monte_carlo_best_of_n, selected_tie_groups


def test_tie_aware_groups_sum_to_one():
    groups = selected_tie_groups([0.0, 1.0, 0.5, 0.25], [2.0, 2.0, 1.0, 0.0], n=3)
    assert math.isclose(sum(group.probability for group in groups), 1.0)
    assert groups[0].indices == (0, 1)
    assert math.isclose(groups[0].mean_utility, 0.5)


def test_exact_law_matches_monte_carlo():
    utilities = [-1.0, 0.0, 0.5, -0.25, 0.75]
    scores = [0.9, 0.2, 0.7, 1.1, 0.1]
    exact = exact_best_of_n_expected_utility(utilities, scores, n=5)
    empirical = monte_carlo_best_of_n(utilities, scores, n=5, trials=40_000, seed=12)
    assert abs(exact - empirical) < 0.02

