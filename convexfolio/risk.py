"""Polymorphic risk measures for the v2 API."""

from __future__ import annotations

import numpy as np

from convexfolio.config import PortfolioInputs
from convexfolio.domain import RiskEvaluation
from convexfolio.errors import ValidationError
from convexfolio.interfaces import RiskMeasure
from convexfolio.math import CFVaR2nd, CFVaR3rd


class VarianceRisk(RiskMeasure):
    """Evaluate the quadratic portfolio variance."""

    name = "variance"

    def __init__(self, inputs: PortfolioInputs) -> None:
        self.inputs = inputs

    def evaluate(self, weights: np.ndarray) -> RiskEvaluation:
        """Return ``0.5 * weights.T * Q * weights``."""
        values = np.asarray(weights, dtype=float)
        if values.shape != self.inputs.cost_vector.shape:
            raise ValidationError("weights do not match portfolio dimensions")
        value = float(0.5 * values @ self.inputs.precision_matrix @ values)
        if not np.isfinite(value):
            raise ValidationError("variance evaluation was not finite")
        return RiskEvaluation(value=value, name=self.name, finite=True)


class CFVaR2Risk(RiskMeasure):
    """Evaluate second-order CFVaR for validated portfolio inputs."""

    name = "cfvar2"

    def __init__(self, inputs: PortfolioInputs, alpha: float) -> None:
        if not np.isfinite(alpha) or not 0.0 < alpha < 0.5:
            raise ValidationError("alpha must satisfy 0 < alpha < 0.5")
        self.inputs = inputs
        self.alpha = float(alpha)

    def evaluate(self, weights: np.ndarray) -> RiskEvaluation:
        """Return the second-order CFVaR value."""
        values = np.asarray(weights, dtype=float)
        if values.shape != self.inputs.cost_vector.shape:
            raise ValidationError("weights do not match portfolio dimensions")
        value = CFVaR2nd(
            alpha=self.alpha,
            expected_payoff=self.inputs.expected_payoff,
            precision_matrix=self.inputs.precision_matrix,
            weights=values,
        ).value
        if not np.isfinite(value):
            raise ValidationError("CFVaR2 evaluation was not finite")
        return RiskEvaluation(value=float(value), name=self.name, finite=True)


class CFVaR3Risk(RiskMeasure):
    """Evaluate third-order CFVaR with a caller-supplied cumulant."""

    name = "cfvar3"

    def __init__(self, inputs: PortfolioInputs, alpha: float) -> None:
        if not np.isfinite(alpha) or not 0.0 < alpha < 0.5:
            raise ValidationError("alpha must satisfy 0 < alpha < 0.5")
        self.inputs = inputs
        self.alpha = float(alpha)

    def evaluate(self, weights: np.ndarray, cumulant: float = 0.0) -> RiskEvaluation:
        """Return third-order CFVaR for a supplied third cumulant."""
        values = np.asarray(weights, dtype=float)
        if values.shape != self.inputs.cost_vector.shape:
            raise ValidationError("weights do not match portfolio dimensions")
        if not np.isfinite(cumulant):
            raise ValidationError("cumulant must be finite")
        value = CFVaR3rd(
            alpha=self.alpha,
            expected_payoff=self.inputs.expected_payoff,
            precision_matrix=self.inputs.precision_matrix,
            weights=values,
            cumulant=float(cumulant),
        ).value
        if not np.isfinite(value):
            raise ValidationError("CFVaR3 evaluation was not finite")
        return RiskEvaluation(value=float(value), name=self.name, finite=True)


__all__ = ["CFVaR2Risk", "CFVaR3Risk", "VarianceRisk"]
