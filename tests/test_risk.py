import numpy as np

from options.math import CFVaR2nd, CFVaR3rd, Quadratic, shapes


def test_shapes_raises_on_incompatible_dims() -> None:
    expected_payoff = np.ones(3)
    precision_matrix = np.eye(4)
    weights = np.ones(3)
    with np.testing.assert_raises(ValueError):
        shapes(expected_payoff, precision_matrix, weights)


def test_variance_quadratic_non_negative_for_psd_q() -> None:
    weights = np.array([1.0, -2.0, 0.5])
    precision_matrix = np.eye(3)
    assert Quadratic(precision_matrix, weights).value >= 0.0


def test_cfvar3_reduces_to_cfvar2_when_kappa3_zero() -> None:
    expected_payoff = np.array([0.2, -0.1, 0.3])
    precision_matrix = np.array([[2.0, 0.1, 0.0], [0.1, 1.5, 0.2], [0.0, 0.2, 1.2]])
    weights = np.array([0.5, 0.2, 0.1])
    alpha = 0.05
    second = CFVaR2nd(alpha, expected_payoff, precision_matrix, weights).value
    third = CFVaR3rd(alpha, expected_payoff, precision_matrix, weights, 0.0).value
    assert np.isclose(second, third, atol=1e-10)
