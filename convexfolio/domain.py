"""Validated domain models for the Convexfolio v2 API."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from convexfolio.config import PortfolioInputs
from convexfolio.errors import ValidationError


@dataclass(frozen=True)
class TolerancePolicy:
    """Numerical tolerances and solver limits used by v2 operations."""

    budget: float = 1e-8
    constraint: float = 1e-8
    max_iterations: int = 1_000

    def __post_init__(self) -> None:
        """Validate the tolerance policy."""
        if not np.isfinite(self.budget) or self.budget <= 0.0:
            raise ValidationError("budget tolerance must be positive and finite")
        if not np.isfinite(self.constraint) or self.constraint <= 0.0:
            raise ValidationError("constraint tolerance must be positive and finite")
        if self.max_iterations < 1:
            raise ValidationError("max_iterations must be positive")


@dataclass(frozen=True)
class ConstraintResult:
    """Feasibility result for one named constraint."""

    name: str
    residual: float
    feasible: bool
    tolerance: float


@dataclass(frozen=True)
class RiskEvaluation:
    """Risk value and validity metadata for a portfolio."""

    value: float
    name: str
    finite: bool
    diagnostics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class OptimizationProblem:
    """Portfolio inputs, constraints, and numerical policy for a solve."""

    inputs: PortfolioInputs
    constraints: tuple[object, ...] = ()
    tolerances: TolerancePolicy = field(default_factory=TolerancePolicy)


@dataclass(frozen=True)
class OptimizationResult:
    """Validated output of an optimizer."""

    weights: np.ndarray
    objective: float
    feasible: bool
    status: str
    diagnostics: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Copy weights so result state cannot alias solver memory."""
        weights = np.array(self.weights, dtype=float, copy=True)
        if weights.ndim != 1 or not np.all(np.isfinite(weights)):
            raise ValidationError(
                "optimization weights must be finite and one-dimensional"
            )
        if not np.isfinite(self.objective):
            raise ValidationError("optimization objective must be finite")
        object.__setattr__(self, "weights", weights)


__all__ = [
    "ConstraintResult",
    "OptimizationProblem",
    "OptimizationResult",
    "RiskEvaluation",
    "TolerancePolicy",
]
