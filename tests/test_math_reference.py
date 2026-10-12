"""Independent reference checks for the legacy numerical primitives."""

import math

import numpy as np
import pytest
from scipy.stats import norm

from convexfolio.math import (
    Bilinear,
    CFVaR2Closed,
    CFVaR2nd,
    CFVaR3rd,
    Compute,
    Cross,
    Cumulant,
    Curvature,
    Expect,
    Linear,
    Linearize,
    Loss,
    Minimize,
    OptimalEpsilon,
    Quadratic,
    QualityScore,
    Score,
    Variance,
)


def test_scalar_and_quadratic_primitives_match_direct_formulas() -> None:
    degrees_of_freedom = 8.0
    expected_coefficient = math.sqrt(degrees_of_freedom / math.pi) * math.gamma(
        (degrees_of_freedom - 1.0) / 2.0
    ) / math.gamma(degrees_of_freedom / 2.0)
    assert Compute(degrees_of_freedom).value == pytest.approx(expected_coefficient)

    covariance = np.array([[2.0, 0.1], [0.1, 1.5]])
    skewness = np.array([0.2, -0.1])
    weights = np.array([0.4, 0.6])
    assert np.allclose(
        Linear(covariance, skewness).value,
        covariance @ skewness / math.sqrt(1.0 + skewness @ covariance @ skewness),
    )
    assert Expect(skewness, weights).value == pytest.approx(skewness @ weights)
    assert Quadratic(covariance, weights).value == pytest.approx(
        0.5 * weights @ covariance @ weights
    )
    assert Variance(covariance)(weights) == pytest.approx(
        Quadratic(covariance, weights).value
    )


def test_curvature_bilinear_and_cross_have_expected_relationship() -> None:
    third_derivative = np.array(
        [
            [[1.0, 0.2], [0.2, 2.0]],
            [[0.5, 0.1], [0.1, 1.0]],
        ]
    )
    h = np.array([0.3, -0.2])
    delta_matrix = np.eye(2)
    budget_matrix = np.array([[0.2, 0.0], [0.0, 0.1]])
    covariance = np.array([[1.2, 0.1], [0.1, 0.9]])
    curvature = Curvature(third_derivative, h).values
    assert np.allclose(
        curvature,
        [float(h @ third_derivative[index] @ h) for index in range(2)],
    )
    bilinear = Bilinear(
        delta_matrix, budget_matrix, covariance, third_derivative, h
    ).matrix
    cross = Cross(
        delta_matrix, budget_matrix, covariance, third_derivative, h
    ).matrix
    assert cross.shape == bilinear.T.shape
    assert np.allclose(cross, bilinear.T)


def test_cfvar2_matches_independent_definition_and_cfvar3_zero_cumulant() -> None:
    alpha = 0.05
    expected_payoff = np.array([0.2, -0.1])
    precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
    weights = np.array([0.4, 0.6])
    variance = 0.5 * weights @ precision_matrix @ weights
    expected = -(expected_payoff @ weights) - norm.ppf(alpha) * math.sqrt(variance)
    assert CFVaR2nd(
        alpha, expected_payoff, precision_matrix, weights
    ).value == pytest.approx(expected)
    assert CFVaR3rd(
        alpha, expected_payoff, precision_matrix, weights, 0.0
    ).value == pytest.approx(expected)


def test_closed_form_and_quality_score_are_budget_feasible() -> None:
    precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
    expected_payoff = np.array([0.2, 0.1])
    cost_vector = np.array([0.6, 0.4])
    weights = Minimize(Variance(precision_matrix), cost_vector).value
    inverse_times_cost = np.linalg.solve(precision_matrix, cost_vector)
    expected_weights = inverse_times_cost / (cost_vector @ inverse_times_cost)
    assert np.allclose(weights, expected_weights)
    closed_weights = CFVaR2Closed(
        precision_matrix, expected_payoff, cost_vector, 0.05
    ).value
    assert closed_weights @ cost_vector == pytest.approx(1.0, abs=1e-8)
    assert QualityScore(
        0.05, expected_payoff, cost_vector, precision_matrix
    ).value == pytest.approx(
        CFVaR2nd(0.05, expected_payoff, precision_matrix, closed_weights).value
    )


def test_score_and_loss_handle_non_positive_loss() -> None:
    loss = Loss(1.0, 0.0, 1.0)
    assert loss(2.0) == pytest.approx(5.0)
    score = Score(1.0, 0.0, -1.0, norm.ppf(0.05))
    assert math.isinf(score(0.0))


def test_cumulant_and_linearize_return_finite_structures() -> None:
    weights = np.array([0.3, 0.7])
    expected_payoff = np.array([0.2, 0.1])
    covariance = np.eye(2)
    delta_matrix = np.array([[0.1, 0.2], [0.3, 0.4]])
    budget_matrix = np.zeros((2, 2))
    third_derivative = np.array(
        [
            [[0.1, 0.0], [0.0, 0.2]],
            [[0.2, 0.0], [0.0, 0.3]],
        ]
    )
    cumulant = Cumulant(
        weights,
        8.0,
        expected_payoff,
        np.eye(2),
        delta_matrix,
        budget_matrix,
        covariance,
        np.zeros((2, 2, 2)),
    )
    assert np.isfinite(cumulant.value)
    linearized = Linearize(
        price_drift=np.array([0.01, 0.02]),
        delta_matrix=delta_matrix,
        third_derivative=third_derivative,
        expected_payoff=expected_payoff,
        covariance=covariance,
        degrees_of_freedom=8.0,
        skewness=np.array([0.1, -0.1]),
        time_increment=1.0,
    )
    assert linearized.dual_residual.shape == (2,)
    assert linearized.precision_matrix.shape == (2, 2)
    assert np.all(np.isfinite(linearized.precision_matrix))


def test_optimal_epsilon_fallback_is_finite() -> None:
    result = OptimalEpsilon(
        alpha=0.05,
        expected_payoff=np.array([0.2, 0.1]),
        cost_vector=np.array([0.6, 0.4]),
        precision_matrix=np.array([[2.0, 0.1], [0.1, 1.5]]),
    )
    assert np.isfinite(result.value)
