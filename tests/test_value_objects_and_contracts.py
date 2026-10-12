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


def test_matrix_validation_reports_each_failure_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        Matrix(np.empty((0, 0)))
    with pytest.raises(ValidationError, match="finite"):
        Matrix([[np.nan]]).validate()
    with pytest.raises(ValidationError, match="symmetric"):
        Matrix([[1.0, 2.0], [0.0, 1.0]]).validate()
    with pytest.raises(ValidationError, match="positive definite"):
        Matrix([[1.0, 2.0], [2.0, 1.0]]).validate()

    def fail_factorisation(values):
        raise np.linalg.LinAlgError("synthetic factorisation failure")

    monkeypatch.setattr(np.linalg, "eigvalsh", fail_factorisation)
    with pytest.raises(ValidationError, match="factorised"):
        Matrix([[1.0]]).validate()


def test_matrix_validation_rejects_ill_conditioned_values() -> None:
    """Numerical inputs with unstable solves fail at the value boundary."""
    with pytest.raises(ValidationError, match="ill-conditioned"):
        Matrix(np.diag([1.0, 1e-13])).validate()
    with pytest.raises(ValidationError, match="greater than 1"):
        Matrix(np.eye(2)).validate(max_condition_number=1.0)


def test_constraint_models_expose_named_residuals() -> None:
    values = np.array([1.0, 1.0])
    assert BudgetConstraint(np.array([0.6, 0.4])).residual(values) == pytest.approx(0)
    assert LongOnlyConstraint().residual(values) == pytest.approx(1)
    assert PositionLimitConstraint(1.5).residual(values) == pytest.approx(0.5)
    assert LeverageConstraint(3.0).residual(values) == pytest.approx(1.0)


def test_constraint_models_reject_invalid_shapes_and_limits() -> None:
    with pytest.raises(ValidationError, match="finite"):
        BudgetConstraint(np.array([np.nan]))
    with pytest.raises(ValidationError, match="positive"):
        BudgetConstraint(np.array([0.0]))
    with pytest.raises(ValidationError, match="matching shapes"):
        BudgetConstraint(np.array([1.0, 1.0])).residual(np.array([1.0]))
    with pytest.raises(ValidationError, match="non-empty"):
        LongOnlyConstraint().residual(np.array([]))
    with pytest.raises(ValidationError, match="non-negative"):
        PositionLimitConstraint(-1.0)
    with pytest.raises(ValidationError, match="non-negative"):
        LeverageConstraint(-1.0)
    with pytest.raises(ValidationError, match="non-empty"):
        PositionLimitConstraint(1.0).residual(np.array([]))


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

