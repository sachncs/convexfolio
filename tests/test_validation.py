"""Boundary validation and constraint contract tests."""

import numpy as np
import pytest

from convexfolio import Matrix, PortfolioInputs, ValidationError, Vector
from convexfolio.constraints import (
    bounds,
    fun_of,
    leverage_cap_inequality,
    sector_caps_inequalities,
)


def valid_inputs() -> PortfolioInputs:
    """Build a small valid portfolio fixture."""
    return PortfolioInputs(
        expected_payoff=np.array([0.1, 0.2, 0.3]),
        cost_vector=np.array([0.5, 0.3, 0.2]),
        precision_matrix=np.eye(3),
    )


def test_portfolio_inputs_copy_arrays() -> None:
    """Mutating caller arrays does not mutate the validated model."""
    inputs = valid_inputs()
    original = inputs.cost_vector.copy()
    with pytest.raises(ValueError, match="read-only"):
        inputs.cost_vector[0] = 99.0
    assert np.array_equal(inputs.cost_vector[1:], original[1:])


def test_value_objects_expose_copy_and_validate() -> None:
    """Vectors and matrices own their validation and copy behavior."""
    vector = Vector([1.0, 2.0]).validate("weights")
    matrix = Matrix([[2.0, 0.0], [0.0, 1.0]]).validate("precision_matrix")
    vector_copy = vector.copy()
    matrix_copy = matrix.copy()
    assert isinstance(vector_copy, Vector)
    assert isinstance(matrix_copy, Matrix)
    vector_copy[0] = 3.0
    matrix_copy[0, 0] = 3.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"expected_payoff": [0.1], "cost_vector": [1.0, 1.0]},
        {
            "expected_payoff": [0.1, 0.2],
            "cost_vector": [1.0, 1.0],
            "precision_matrix": [[1.0]],
        },
        {"expected_payoff": [0.1, 0.2], "cost_vector": [1.0, 0.0]},
        {
            "expected_payoff": [0.1, 0.2],
            "cost_vector": [1.0, 1.0],
            "precision_matrix": [[1.0, 2.0], [2.0, 1.0]],
        },
    ],
)
def test_portfolio_inputs_reject_invalid_data(kwargs: dict[str, object]) -> None:
    """Invalid shapes, prices, and matrices fail at the boundary."""
    values: dict[str, object] = {
        "expected_payoff": [0.1, 0.2],
        "cost_vector": [1.0, 1.0],
        "precision_matrix": [[1.0, 0.0], [0.0, 1.0]],
    }
    values.update(kwargs)
    with pytest.raises(ValidationError):
        PortfolioInputs(**values)  # type: ignore[arg-type]


def test_sector_caps_use_instrument_dimension() -> None:
    """Each sector constraint accepts the complete instrument vector."""
    constraints = sector_caps_inequalities([0, 0, 1], 0.8)
    assert len(constraints) == 2
    assert fun_of(constraints[0])(np.array([0.2, 0.2, 0.6])) == pytest.approx(0.4)


def test_leverage_cap_uses_absolute_exposure() -> None:
    """Long and short positions both count toward leverage."""
    constraint = leverage_cap_inequality(2, 1.0)
    residual = fun_of(constraint)
    assert residual(np.array([0.8, -0.4])) == pytest.approx(-0.2)


def test_bounds_reject_invalid_range() -> None:
    """Bounds require a finite ordered range."""
    with pytest.raises(ValidationError):
        bounds(1.0, 0.0, 2)
