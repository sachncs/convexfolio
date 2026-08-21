"""Tests for convexfolio.constraints and constraint-aware solvers."""

from __future__ import annotations

import numpy as np

from convexfolio.constraints import (
    bounds,
    budget,
    budget_with_extras,
    fun_of,
    inequality,
    leverage_cap_inequality,
    long_only_bounds,
    long_only_inequalities,
    merge,
    position_limits_bounds,
    position_limits_inequalities,
    sector_caps_inequalities,
)
from convexfolio.math import CFVaR3Numerical, CFVaR3Objective, Variance


def test_budget_constraint_evaluates_to_zero_at_feasible_point() -> None:
    v = np.array([0.6, 0.4])
    c = budget(v)
    assert c["type"] == "eq"
    feasible = np.array([1.0, 1.0])  # 1*0.6 + 1*0.4 = 1.0
    assert abs(float(fun_of(c)(feasible))) < 1e-12
    # At an infeasible point, the residual should be non-zero.
    assert abs(float(fun_of(c)(np.array([2.0, 0.0])))) > 1e-6


def test_bounds_length_matches_n() -> None:
    assert len(bounds(-1.0, 1.0, 5)) == 5
    assert all(lo == -1.0 and hi == 1.0 for lo, hi in bounds(-1.0, 1.0, 3))


def test_inequality_constraint_is_le() -> None:
    a = np.array([1.0, 0.0, 0.0])
    c = inequality(a, 1.0)
    assert c["type"] == "ineq"
    assert float(fun_of(c)(np.array([0.5, 0.0, 0.0]))) > 0
    assert float(fun_of(c)(np.array([2.0, 0.0, 0.0]))) < 0


def test_merge_flattens_groups() -> None:
    v = np.array([1.0, 1.0])
    a = np.array([1.0, 0.0])
    merged = merge((budget(v),), (inequality(a, 0.5),))
    assert len(merged) == 2
    assert merged[0]["type"] == "eq"
    assert merged[1]["type"] == "ineq"


def test_budget_with_extras_appends() -> None:
    v = np.array([1.0, 1.0])
    a = np.array([1.0, 0.0])
    out = budget_with_extras(v, inequality(a, 0.5))
    assert len(out) == 2
    assert out[0]["type"] == "eq"


def test_long_only_inequalities_count() -> None:
    constraints = long_only_inequalities(4)
    assert len(constraints) == 4
    for c in constraints:
        assert c["type"] == "ineq"


def test_long_only_bounds_are_non_negative() -> None:
    b = long_only_bounds(3)
    for lo, hi in b:
        assert lo == 0.0
        assert hi == float("inf")


def test_position_limits_inequalities_count() -> None:
    constraints = position_limits_inequalities(3, 0.3)
    assert len(constraints) == 6  # 2 per instrument


def test_position_limits_bounds_match() -> None:
    b = position_limits_bounds(3, 0.5)
    for lo, hi in b:
        assert lo == -0.5
        assert hi == 0.5


def test_sector_caps_one_per_sector() -> None:
    sector_map = [0, 0, 1, 1, 2]
    constraints = sector_caps_inequalities(sector_map, max_per_sector=0.6)
    assert len(constraints) == 3  # sectors 0, 1, 2


def test_sector_caps_evaluate_correctly() -> None:
    sector_map = [0, 0, 1, 1]
    constraints = sector_caps_inequalities(sector_map, max_per_sector=0.5)
    feasible = np.array([0.3, 0.2, 0.2, 0.3])
    violations = np.array([0.4, 0.4, 0.4, 0.4])
    for c in constraints:
        assert float(fun_of(c)(feasible)) >= -1e-12
        assert float(fun_of(c)(violations)) < 0


def test_leverage_cap_is_one_constraint() -> None:
    c = leverage_cap_inequality(5, 1.5)
    assert c["type"] == "ineq"
    assert float(fun_of(c)(np.array([0.5, 0.3, 0.2, 0.2, 0.1]))) > 0
    assert float(fun_of(c)(np.array([1.0, 1.0, 0.0, 0.0, 0.0]))) < 0


def test_cfvar3_with_long_only_constraint() -> None:
    rng = np.random.default_rng(7)
    n = 4
    sample = rng.normal(size=(n, n))
    precision_matrix = sample.T @ sample + 0.5 * np.eye(n)
    cost_vector = np.abs(rng.normal(size=n)) + 0.1
    expected_payoff = rng.normal(size=n)
    objective = CFVaR3Objective(
        alpha=0.05,
        expected_payoff=expected_payoff,
        precision_matrix=precision_matrix,
        kappa3_callback=lambda x: 0.0,
    )
    weights = CFVaR3Numerical(
        cost_vector=cost_vector,
        initial_weights=cost_vector / float(cost_vector @ cost_vector),
        objective_callable=objective,
        extra_constraints=tuple(long_only_inequalities(n)),
    ).value
    assert np.all(weights >= -1e-8), f"weights {weights} should be >= 0"
    assert np.isclose(float(weights @ cost_vector), 1.0, atol=1e-6)


def test_cfvar3_with_sector_caps() -> None:
    rng = np.random.default_rng(11)
    n = 6
    sample = rng.normal(size=(n, n))
    precision_matrix = sample.T @ sample + 0.5 * np.eye(n)
    cost_vector = np.abs(rng.normal(size=n)) + 0.1
    expected_payoff = rng.normal(size=n)
    objective = CFVaR3Objective(
        alpha=0.05,
        expected_payoff=expected_payoff,
        precision_matrix=precision_matrix,
        kappa3_callback=lambda x: 0.0,
    )
    sector_map = [0, 0, 1, 1, 2, 2]
    constraints = list(
        long_only_inequalities(n)
        + sector_caps_inequalities(sector_map, max_per_sector=0.4)
    )
    weights = CFVaR3Numerical(
        cost_vector=cost_vector,
        initial_weights=cost_vector / float(cost_vector @ cost_vector),
        objective_callable=objective,
        extra_constraints=tuple(constraints),
    ).value
    assert np.all(weights >= -1e-8)
    assert np.isclose(float(weights @ cost_vector), 1.0, atol=1e-6)
    for sector in {0, 1, 2}:
        indices = [i for i, s in enumerate(sector_map) if s == sector]
        sector_sum = float(sum(weights[i] for i in indices))
        assert sector_sum <= 0.4 + 1e-6, f"sector {sector} sum {sector_sum} > 0.4"


def test_cfvar3_backward_compat_no_extras() -> None:
    """Old callers without extra_constraints still work."""
    rng = np.random.default_rng(13)
    n = 3
    sample = rng.normal(size=(n, n))
    precision_matrix = sample.T @ sample + 0.5 * np.eye(n)
    cost_vector = np.abs(rng.normal(size=n)) + 0.1
    expected_payoff = rng.normal(size=n)
    objective = CFVaR3Objective(
        alpha=0.05,
        expected_payoff=expected_payoff,
        precision_matrix=precision_matrix,
        kappa3_callback=lambda x: 0.0,
    )
    weights = CFVaR3Numerical(
        cost_vector=cost_vector,
        initial_weights=cost_vector / float(cost_vector @ cost_vector),
        objective_callable=objective,
    ).value
    assert np.isclose(float(weights @ cost_vector), 1.0, atol=1e-6)


def test_variance_unchanged_by_constraints_module() -> None:
    """Variance objective is unaffected; constraint module is orthogonal."""
    Q = np.eye(3)
    v = np.array([0.5, 0.5, 0.5])
    var = Variance(Q)
    assert abs(float(var(v)) - 0.375) < 1e-12
