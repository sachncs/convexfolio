"""Polymorphic optimizers for the v2 API."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from convexfolio.domain import ConstraintResult, OptimizationProblem, OptimizationResult
from convexfolio.errors import InfeasibleProblemError, SolverFailureError
from convexfolio.interfaces import Constraint, Optimizer, RiskMeasure


class ClosedFormVarianceOptimizer(Optimizer):
    """Solve unconstrained variance minimization under a budget constraint."""

    def solve(
        self, problem: OptimizationProblem, risk_measure: RiskMeasure
    ) -> OptimizationResult:
        """Return validated weights from a stable linear solve."""
        inputs = problem.inputs
        inverse_times_cost = np.linalg.solve(
            inputs.precision_matrix, inputs.cost_vector
        )
        denominator = float(inputs.cost_vector @ inverse_times_cost)
        if not np.isfinite(denominator) or denominator <= 0.0:
            raise SolverFailureError("variance problem has an invalid normalization")
        weights = inverse_times_cost / denominator
        constraint_results = check_constraints(problem, weights)
        infeasible = [item.name for item in constraint_results if not item.feasible]
        if infeasible:
            raise InfeasibleProblemError(
                "closed-form solution violates constraints: " + ", ".join(infeasible)
            )
        evaluation = risk_measure.evaluate(weights)
        return OptimizationResult(
            weights=weights,
            objective=evaluation.value,
            feasible=True,
            status="optimal",
            diagnostics={
                "risk_measure": evaluation.name,
                "constraints": [item.__dict__ for item in constraint_results],
            },
        )


class SlsqpOptimizer(Optimizer):
    """Solve a constrained problem with SciPy's SLSQP implementation."""

    def solve(
        self, problem: OptimizationProblem, risk_measure: RiskMeasure
    ) -> OptimizationResult:
        """Solve and validate a constrained risk minimization problem."""
        constraints = []
        for constraint in problem.constraints:
            if not isinstance(constraint, Constraint):
                raise TypeError("optimization constraints must implement Constraint")
            constraints.append(
                {
                    "type": "eq" if constraint.kind == "equality" else "ineq",
                    "fun": constraint.residual,
                }
            )
        if not any(item["type"] == "eq" for item in constraints):
            raise InfeasibleProblemError("an equality budget constraint is required")

        costs = problem.inputs.cost_vector
        initial_weights = costs / float(costs @ costs)

        def objective(weights: np.ndarray) -> float:
            return risk_measure.evaluate(weights).value

        result = minimize(
            objective,
            x0=initial_weights,
            method="SLSQP",
            constraints=constraints,
            options={"maxiter": problem.tolerances.max_iterations, "ftol": 1e-9},
        )
        if not result.success:
            raise SolverFailureError(
                f"SLSQP failed after {result.nit} iterations: {result.message}"
            )
        weights = np.asarray(result.x, dtype=float)
        if not np.all(np.isfinite(weights)) or not np.isfinite(result.fun):
            raise SolverFailureError("SLSQP returned non-finite output")
        constraint_results = check_constraints(problem, weights)
        infeasible = [item.name for item in constraint_results if not item.feasible]
        if infeasible:
            raise SolverFailureError(
                "SLSQP returned infeasible weights: " + ", ".join(infeasible)
            )
        return OptimizationResult(
            weights=weights,
            objective=float(result.fun),
            feasible=True,
            status="optimal",
            diagnostics={
                "iterations": int(result.nit),
                "message": str(result.message),
                "constraints": [item.__dict__ for item in constraint_results],
            },
        )
def check_constraints(
    problem: OptimizationProblem, weights: np.ndarray
) -> list[ConstraintResult]:
    """Evaluate all constraints through the polymorphic contract."""
    results: list[ConstraintResult] = []
    for constraint in problem.constraints:
        if not isinstance(constraint, Constraint):
            raise TypeError("optimization constraints must implement Constraint")
        results.append(constraint.check(weights, problem.tolerances.constraint))
    return results


__all__ = ["ClosedFormVarianceOptimizer", "SlsqpOptimizer", "check_constraints"]
