import numpy as np
import pytest

from oop.risk import cfvar2
from oop.risk import cfvar3
from oop.risk import validate_shapes
from oop.risk import variance_quadratic


def test_validate_shapes_raises_on_incompatible_dims() -> None:
    expected_payoff = np.ones(3)
    precision_matrix = np.eye(4)
    weights = np.ones(3)
    with pytest.raises(ValueError):
        validate_shapes(expected_payoff, precision_matrix, weights)


def test_variance_quadratic_non_negative_for_psd_q() -> None:
    weights = np.array([1.0, -2.0, 0.5])
    precision_matrix = np.eye(3)
    assert variance_quadratic(precision_matrix, weights) >= 0.0


def test_cfvar3_reduces_to_cfvar2_when_kappa3_zero() -> None:
    expected_payoff = np.array([0.2, -0.1, 0.3])
    precision_matrix = np.array(
        [[2.0, 0.1, 0.0], [0.1, 1.5, 0.2], [0.0, 0.2, 1.2]]
    )
    weights = np.array([0.5, 0.2, 0.1])
    assert np.isclose(
        cfvar2(0.05, expected_payoff, precision_matrix, weights),
        cfvar3(0.05, expected_payoff, precision_matrix, weights, 0.0),
        atol=1e-10,
    )
