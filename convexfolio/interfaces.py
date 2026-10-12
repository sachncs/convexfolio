"""Polymorphic contracts for risk measures, constraints, and optimizers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from convexfolio.domain import (
    ConstraintResult,
    OptimizationProblem,
    OptimizationResult,
    RiskEvaluation,
)


class RiskMeasure(ABC):
    """Interface for a portfolio risk evaluator."""

    name: str

    @abstractmethod
    def evaluate(self, weights: np.ndarray) -> RiskEvaluation:
        """Evaluate risk for one weight vector."""


class Constraint(ABC):
    """Interface for a portfolio feasibility constraint."""

    name: str
    kind: str

    @abstractmethod
    def residual(self, weights: np.ndarray) -> float:
        """Return a non-negative feasibility residual when satisfied."""

    def check(self, weights: np.ndarray, tolerance: float) -> ConstraintResult:
        """Evaluate feasibility using a caller-supplied tolerance."""
        residual = float(self.residual(weights))
        return ConstraintResult(
            name=self.name,
            residual=residual,
            feasible=residual >= -tolerance,
            tolerance=tolerance,
        )


class Optimizer(ABC):
    """Interface for a constrained portfolio optimizer."""

    @abstractmethod
    def solve(
        self, problem: OptimizationProblem, risk_measure: RiskMeasure
    ) -> OptimizationResult:
        """Solve a portfolio problem for the selected risk measure."""


__all__ = ["Constraint", "Optimizer", "RiskMeasure"]
