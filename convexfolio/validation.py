"""Internal validation primitives shared by package boundaries."""

from __future__ import annotations

from convexfolio.arrays import Matrix, Vector
from convexfolio.errors import ValidationError


def validate_portfolio_dimensions(
    expected_payoff: Vector,
    cost_vector: Vector,
    precision_matrix: Matrix,
) -> None:
    """Validate that portfolio vectors match the precision matrix."""
    instrument_count = cost_vector.shape[0]
    if expected_payoff.shape[0] != instrument_count:
        raise ValidationError(
            "expected_payoff and cost_vector must have the same length"
        )
    if precision_matrix.shape != (instrument_count, instrument_count):
        raise ValidationError(
            "precision_matrix dimensions must match the portfolio vectors"
        )


__all__ = ["validate_portfolio_dimensions"]
