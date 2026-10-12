"""Contract tests for the polymorphic v2 API."""

import numpy as np
import pytest

from convexfolio import (
    BudgetConstraint,
    ClosedFormVarianceOptimizer,
    LongOnlyConstraint,
    OptimizationProblem,
    PortfolioInputs,
    TolerancePolicy,
    VarianceRisk,
)


def portfolio() -> PortfolioInputs:
    """Return a valid two-instrument portfolio."""
    return PortfolioInputs(
        expected_payoff=np.array([0.2, 0.1]),
        cost_vector=np.array([0.6, 0.4]),
        precision_matrix=np.array([[2.0, 0.1], [0.1, 1.5]]),
    )


def test_polymorphic_optimizer_returns_diagnostics() -> None:
    """The optimizer consumes interfaces and returns a structured result."""
    inputs = portfolio()
    problem = OptimizationProblem(
        inputs=inputs,
        constraints=(BudgetConstraint(inputs.cost_vector), LongOnlyConstraint()),
        tolerances=TolerancePolicy(),
    )
    result = ClosedFormVarianceOptimizer().solve(problem, VarianceRisk(inputs))
    assert result.status == "optimal"
    assert result.feasible
    assert result.weights @ inputs.cost_vector == pytest.approx(1.0)
    assert result.diagnostics["risk_measure"] == "variance"


def test_polymorphic_optimizer_uses_constraints() -> None:
    """The optimizer evaluates every supplied constraint contract."""
    inputs = portfolio()
    problem = OptimizationProblem(
        inputs=inputs,
        constraints=(BudgetConstraint(inputs.cost_vector), LongOnlyConstraint()),
    )
    result = ClosedFormVarianceOptimizer().solve(problem, VarianceRisk(inputs))
    assert result.feasible
    constraints = result.diagnostics["constraints"]
    assert isinstance(constraints, list)
    assert {item["name"] for item in constraints} == {"budget", "long_only"}


def test_risk_measure_is_polymorphic() -> None:
    """The same problem can accept a risk implementation by contract."""
    inputs = portfolio()
    evaluation = VarianceRisk(inputs).evaluate(np.array([1.0, 1.0]))
    assert evaluation.name == "variance"
    assert evaluation.finite
