import numpy as np
import pytest

from options.math import second_order_risk
from options.math import third_order_risk
from options.math import shapes
from options.math import quadratic


def test_shapes_raises_on_incompatible_dims() -> None:
    expected_payoff = np.ones(3)
    precision_matrix = np.eye(4)
    weights = np.ones(3)
    with pytest.raises(ValueError):
        shapes(expected_payoff, precision_matrix, weights)


def test_quadratic_non_negative_for_psd_q() -> None:
    weights = np.array([1.0, -2.0, 0.5])
    precision_matrix = np.eye(3)
    assert quadratic(precision_matrix, weights) >= 0.0


def test_cfvar3_reduces_to_cfvar2_when_kappa3_zero() -> None:
    expected_payoff = np.array([0.2, -0.1, 0.3])
    precision_matrix = np.array(
        [[2.0, 0.1, 0.0], [0.1, 1.5, 0.2], [0.0, 0.2, 1.2]]
    )
    weights = np.array([0.5, 0.2, 0.1])
    assert np.isclose(
        second_order_risk(0.05, expected_payoff, precision_matrix, weights),
        third_order_risk(0.05, expected_payoff, precision_matrix, weights, 0.0),
        atol=1e-10,
    )
