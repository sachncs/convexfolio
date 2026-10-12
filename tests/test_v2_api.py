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
from convexfolio.domain import ConstraintResult, OptimizationResult, RiskEvaluation
from convexfolio.errors import ValidationError


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


def test_domain_results_validate_and_copy_inputs() -> None:
    source = np.array([0.4, 0.6])
    result = OptimizationResult(source, 1.0, True, "optimal")
    source[0] = 99.0
    assert result.weights[0] == pytest.approx(0.4)
    assert ConstraintResult("budget", 0.0, True, 1e-8).feasible
    assert RiskEvaluation(1.0, "variance", True).finite
    with pytest.raises(ValidationError, match="finite"):
        OptimizationResult(np.array([np.nan]), 1.0, False, "failed")
    with pytest.raises(ValidationError, match="objective"):
        OptimizationResult(np.array([1.0]), np.inf, False, "failed")


def test_equality_constraints_require_zero_residual() -> None:
    constraint = BudgetConstraint(np.array([0.6, 0.4]))
    assert constraint.check(np.array([1.0, 1.0]), 1e-8).feasible
    assert not constraint.check(np.array([0.0, 0.0]), 1e-8).feasible


def test_tolerance_policy_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError, match="budget tolerance"):
        TolerancePolicy(budget=0.0)
    with pytest.raises(ValidationError, match="constraint tolerance"):
        TolerancePolicy(constraint=np.inf)
    with pytest.raises(ValidationError, match="max_iterations"):
        TolerancePolicy(max_iterations=0)
