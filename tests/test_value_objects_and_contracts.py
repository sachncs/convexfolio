"""Coverage for validated value objects and polymorphic domain contracts."""

import numpy as np
import pytest

from convexfolio import Matrix, Vector
from convexfolio.config import PortfolioInputs
from convexfolio.constraint_models import (
    BudgetConstraint,
    LeverageConstraint,
    LongOnlyConstraint,
    PositionLimitConstraint,
)
from convexfolio.errors import ValidationError
from convexfolio.risk import CFVaR2Risk, CFVaR3Risk, VarianceRisk


def inputs() -> PortfolioInputs:
    return PortfolioInputs(
        expected_payoff=np.array([0.2, 0.1]),
        cost_vector=np.array([0.6, 0.4]),
        precision_matrix=np.array([[2.0, 0.1], [0.1, 1.5]]),
    )


def test_vector_and_matrix_copy_are_writable_and_validate_in_place() -> None:
    vector = Vector([1.0, 2.0])
    matrix = Matrix([[2.0, 0.1], [0.1, 1.5]])
    assert not vector.flags.writeable
    assert not matrix.flags.writeable
    writable_vector = vector.copy()
    writable_matrix = matrix.copy()
    writable_vector[0] = 3.0
    writable_matrix[0, 0] = 3.0
    assert vector.validate() is vector
    assert matrix.validate() is matrix


@pytest.mark.parametrize(
    ("factory", "value"),
    [
        (Vector, np.array([])),
        (Vector, np.array([[1.0]])),
        (Vector, np.array([np.nan])),
        (Matrix, np.array([[1.0, 0.0]])),
        (Matrix, np.array([[1.0, 2.0], [2.0, 1.0]])),
    ],
)
def test_value_objects_reject_invalid_values(factory, value) -> None:
    with pytest.raises(ValidationError):
        factory(value).validate()


def test_positive_vector_validation_rejects_zero() -> None:
    with pytest.raises(ValidationError, match="only positive"):
        Vector([0.0]).validate(positive=True)


def test_constraint_models_expose_named_residuals() -> None:
    values = np.array([1.0, 1.0])
    assert BudgetConstraint(np.array([0.6, 0.4])).residual(values) == pytest.approx(0)
    assert LongOnlyConstraint().residual(values) == pytest.approx(1)
    assert PositionLimitConstraint(1.5).residual(values) == pytest.approx(0.5)
    assert LeverageConstraint(3.0).residual(values) == pytest.approx(1.0)


def test_risk_contracts_evaluate_all_risk_measures() -> None:
    portfolio = inputs()
    weights = np.array([1.0, 1.0])
    assert VarianceRisk(portfolio).evaluate(weights).name == "variance"
    assert CFVaR2Risk(portfolio, 0.05).evaluate(weights).name == "cfvar2"
    assert CFVaR3Risk(portfolio, 0.05).evaluate(weights, cumulant=0.01).name == "cfvar3"


@pytest.mark.parametrize("risk_factory", [CFVaR2Risk, CFVaR3Risk])
def test_risk_contracts_reject_invalid_inputs(risk_factory) -> None:
    portfolio = inputs()
    with pytest.raises(ValidationError, match="alpha"):
        risk_factory(portfolio, 0.5)
    with pytest.raises(ValidationError, match="weights"):
        risk_factory(portfolio, 0.05).evaluate(np.array([1.0]))

