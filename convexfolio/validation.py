"""Internal validation primitives shared by package boundaries."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from convexfolio.errors import ValidationError
from convexfolio.types import FloatArray


def copy_float_vector(
    value: Sequence[float] | np.ndarray, name: str
) -> FloatArray:
    """Copy and validate a finite one-dimensional float vector."""
    vector = np.array(value, dtype=float, copy=True)
    if vector.ndim != 1:
        raise ValidationError(f"{name} must be a one-dimensional vector")
    if vector.size == 0:
        raise ValidationError(f"{name} must not be empty")
    if not np.all(np.isfinite(vector)):
        raise ValidationError(f"{name} must contain only finite values")
    return vector


def copy_positive_definite_matrix(
    value: Sequence[Sequence[float]] | np.ndarray, name: str
) -> FloatArray:
    """Copy and validate a finite symmetric positive-definite matrix."""
    matrix = np.array(value, dtype=float, copy=True)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValidationError(f"{name} must be a square matrix")
    if matrix.shape[0] == 0:
        raise ValidationError(f"{name} must not be empty")
    if not np.all(np.isfinite(matrix)):
        raise ValidationError(f"{name} must contain only finite values")
    if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        raise ValidationError(f"{name} must be symmetric")
    try:
        eigenvalues = np.linalg.eigvalsh(matrix)
    except np.linalg.LinAlgError as exc:
        raise ValidationError(f"{name} could not be factorised") from exc
    if float(np.min(eigenvalues)) <= 0.0:
        raise ValidationError(f"{name} must be positive definite")
    return matrix


def validate_portfolio_dimensions(
    expected_payoff: FloatArray,
    cost_vector: FloatArray,
    precision_matrix: FloatArray,
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


def validate_positive_values(vector: FloatArray, name: str) -> None:
    """Require every value in a vector to be strictly positive."""
    if np.any(vector <= 0.0):
        raise ValidationError(f"{name} must contain only positive values")


__all__ = [
    "copy_float_vector",
    "copy_positive_definite_matrix",
    "validate_portfolio_dimensions",
    "validate_positive_values",
]
