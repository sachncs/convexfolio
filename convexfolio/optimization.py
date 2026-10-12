"""Polymorphic optimizers for the v2 API."""

from __future__ import annotations

import numpy as np

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


__all__ = ["ClosedFormVarianceOptimizer", "check_constraints"]
