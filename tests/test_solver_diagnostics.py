"""Solver diagnostics and failure-contract tests."""

import numpy as np
import pytest

from convexfolio import (
    BudgetConstraint,
    CFVaR2Risk,
    LongOnlyConstraint,
    OptimizationProblem,
    PortfolioInputs,
    SlsqpOptimizer,
)
from convexfolio.errors import InfeasibleProblemError, SolverFailureError


def inputs() -> PortfolioInputs:
    """Return a valid portfolio for solver tests."""
    return PortfolioInputs(
        expected_payoff=np.array([0.2, 0.1]),
        cost_vector=np.array([0.6, 0.4]),
        precision_matrix=np.array([[2.0, 0.1], [0.1, 1.5]]),
    )


def test_slsqp_returns_iteration_diagnostics() -> None:
    """A successful solve reports feasibility and iteration metadata."""
    portfolio = inputs()
    problem = OptimizationProblem(
        inputs=portfolio,
        constraints=(BudgetConstraint(portfolio.cost_vector), LongOnlyConstraint()),
    )
    result = SlsqpOptimizer().solve(problem, CFVaR2Risk(portfolio, 0.05))
    assert result.feasible
    assert result.status == "optimal"
    assert result.diagnostics["iterations"] >= 0
    assert result.weights @ portfolio.cost_vector == pytest.approx(1.0, abs=1e-8)


def test_slsqp_requires_budget_constraint() -> None:
    """A solver cannot run without an equality budget contract."""
    portfolio = inputs()
    problem = OptimizationProblem(inputs=portfolio, constraints=(LongOnlyConstraint(),))
    with pytest.raises(InfeasibleProblemError, match="equality budget"):
        SlsqpOptimizer().solve(problem, CFVaR2Risk(portfolio, 0.05))


def test_slsqp_rejects_too_small_iteration_budget() -> None:
    """Non-convergence is surfaced as a typed solver failure."""
    portfolio = inputs()
    problem = OptimizationProblem(
        inputs=portfolio,
        constraints=(BudgetConstraint(portfolio.cost_vector),),
    )
    problem = OptimizationProblem(
        inputs=portfolio,
        constraints=problem.constraints,
        tolerances=problem.tolerances.__class__(max_iterations=1),
    )
    with pytest.raises(SolverFailureError):
        SlsqpOptimizer().solve(problem, CFVaR2Risk(portfolio, 0.05))
