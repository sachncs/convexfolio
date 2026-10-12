"""Concrete polymorphic portfolio constraints."""

from __future__ import annotations

import numpy as np

from convexfolio.errors import ValidationError
from convexfolio.interfaces import Constraint


class BudgetConstraint(Constraint):
    """Require the weighted cost vector to equal one."""

    name = "budget"

    def __init__(self, cost_vector: np.ndarray) -> None:
        costs = np.array(cost_vector, dtype=float, copy=True)
        if costs.ndim != 1 or costs.size == 0 or not np.all(np.isfinite(costs)):
            raise ValidationError("cost_vector must be a finite non-empty vector")
        if np.any(costs <= 0.0):
            raise ValidationError("cost_vector must be strictly positive")
        self.cost_vector = costs

    def residual(self, weights: np.ndarray) -> float:
        """Return signed budget slack, positive when under budget."""
        values = np.asarray(weights, dtype=float)
        if values.shape != self.cost_vector.shape:
            raise ValidationError("weights and cost_vector must have matching shapes")
        return float(1.0 - np.dot(values, self.cost_vector))


class LongOnlyConstraint(Constraint):
    """Require every portfolio weight to be non-negative."""

    name = "long_only"

    def residual(self, weights: np.ndarray) -> float:
        """Return the smallest weight, which must be non-negative."""
        values = np.asarray(weights, dtype=float)
        if values.ndim != 1 or values.size == 0:
            raise ValidationError("weights must be a non-empty vector")
        return float(np.min(values))


class PositionLimitConstraint(Constraint):
    """Require each absolute position to stay below a limit."""

    name = "position_limit"

    def __init__(self, maximum: float) -> None:
        if not np.isfinite(maximum) or maximum < 0.0:
            raise ValidationError("position limit must be finite and non-negative")
        self.maximum = float(maximum)

    def residual(self, weights: np.ndarray) -> float:
        """Return the remaining absolute-position slack."""
        values = np.asarray(weights, dtype=float)
        if values.ndim != 1 or values.size == 0:
            raise ValidationError("weights must be a non-empty vector")
        return float(self.maximum - np.max(np.abs(values)))


class LeverageConstraint(Constraint):
    """Require total absolute exposure to stay below a limit."""

    name = "leverage"

    def __init__(self, maximum: float) -> None:
        if not np.isfinite(maximum) or maximum < 0.0:
            raise ValidationError("leverage limit must be finite and non-negative")
        self.maximum = float(maximum)

    def residual(self, weights: np.ndarray) -> float:
        """Return remaining absolute-leverage slack."""
        values = np.asarray(weights, dtype=float)
        if values.ndim != 1 or values.size == 0:
            raise ValidationError("weights must be a non-empty vector")
        return float(self.maximum - np.sum(np.abs(values)))


__all__ = [
    "BudgetConstraint",
    "LeverageConstraint",
    "LongOnlyConstraint",
    "PositionLimitConstraint",
]
