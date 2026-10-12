"""Numerical edge-case tests for risk and optimizer primitives."""

import numpy as np
import pytest

from convexfolio import CFVaR2nd, CFVaR3rd, Minimize, Variance


def test_risk_evaluators_reject_zero_variance() -> None:
    """Risk evaluation must not divide by zero or return NaN."""
    expected_payoff = np.array([0.1])
    precision_matrix = np.array([[1.0]])
    weights = np.array([0.0])
    with pytest.raises(ValueError, match="variance"):
        CFVaR2nd(0.05, expected_payoff, precision_matrix, weights)
    with pytest.raises(ValueError, match="variance"):
        CFVaR3rd(0.05, expected_payoff, precision_matrix, weights, 0.0)


def test_risk_evaluators_reject_invalid_alpha() -> None:
    """Risk evaluators reject quantile values without finite meaning."""
    with pytest.raises(ValueError, match="alpha"):
        CFVaR2nd(0.0, np.array([0.1]), np.array([[1.0]]), np.array([1.0]))


def test_variance_minimizer_uses_validated_normalization() -> None:
    """The closed-form solver returns a finite budget-feasible result."""
    weights = Minimize(
        Variance(np.array([[2.0, 0.1], [0.1, 1.5]])),
        np.array([0.6, 0.4]),
    ).value
    assert np.all(np.isfinite(weights))
    assert weights @ np.array([0.6, 0.4]) == pytest.approx(1.0)
