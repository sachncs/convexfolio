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
from convexfolio.optimization import check_constraints


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


def test_slsqp_rejects_non_constraint_objects() -> None:
    portfolio = inputs()
    problem = OptimizationProblem(inputs=portfolio, constraints=(object(),))
    with pytest.raises(TypeError, match="implement Constraint"):
        SlsqpOptimizer().solve(problem, CFVaR2Risk(portfolio, 0.05))
    with pytest.raises(TypeError, match="implement Constraint"):
        check_constraints(problem, np.array([1.0, 1.0]))


@pytest.mark.parametrize(
    ("result_values", "message"),
    [
        (
            {
                "success": True,
                "nit": 2,
                "fun": np.inf,
                "message": "bad",
                "x": [1.0, 1.0],
            },
            "non-finite",
        ),
        (
            {"success": True, "nit": 2, "fun": 1.0, "message": "bad", "x": [0.0, 0.0]},
            "infeasible",
        ),
        (
            {
                "success": False,
                "nit": 2,
                "fun": 1.0,
                "message": "failed",
                "x": [1.0, 1.0],
            },
            "failed",
        ),
    ],
)
def test_slsqp_postsolve_failure_paths(
    monkeypatch: pytest.MonkeyPatch, result_values: dict[str, object], message: str
) -> None:
    portfolio = inputs()
    problem = OptimizationProblem(
        inputs=portfolio,
        constraints=(BudgetConstraint(portfolio.cost_vector),),
    )

    class FakeResult:
        success = result_values["success"]
        nit = result_values["nit"]
        fun = result_values["fun"]
        message = result_values["message"]
        x = np.asarray(result_values["x"], dtype=float)

    monkeypatch.setattr(
        "convexfolio.optimization.minimize", lambda *args, **kwargs: FakeResult()
    )
    with pytest.raises(SolverFailureError, match=message):
        SlsqpOptimizer().solve(problem, CFVaR2Risk(portfolio, 0.05))
