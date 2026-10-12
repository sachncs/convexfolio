"""Validated numerical value objects used throughout Convexfolio."""

from __future__ import annotations

from typing import Literal, cast

import numpy as np

from convexfolio.errors import ValidationError


class Vector(np.ndarray):
    """Finite, non-empty one-dimensional floating-point array."""

    def __new__(cls, values: object) -> Vector:
        """Construct an owned vector from array-like input."""
        vector = np.array(values, dtype=float, copy=True)
        if vector.ndim != 1 or vector.size == 0:
            raise ValidationError("vector must be a non-empty one-dimensional array")
        vector.flags.writeable = False
        return vector.view(cls)

    def copy(self, order: Literal["K", "A", "C", "F"] | None = None) -> Vector:
        """Return an owned copy that retains the Vector type."""
        copied = np.asarray(self, dtype=float).copy(order=order)
        return cast(Vector, copied.view(Vector))

    def validate(self, name: str = "vector", positive: bool = False) -> Vector:
        """Validate finiteness and optionally strict positivity in place."""
        if not np.all(np.isfinite(self)):
            raise ValidationError(f"{name} must contain only finite values")
        if positive and np.any(self <= 0.0):
            raise ValidationError(f"{name} must contain only positive values")
        return self


class Matrix(np.ndarray):
    """Finite symmetric positive-definite two-dimensional array."""

    def __new__(cls, values: object) -> Matrix:
        """Construct an owned matrix from array-like input."""
        matrix = np.array(values, dtype=float, copy=True)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValidationError("matrix must be square")
        if matrix.shape[0] == 0:
            raise ValidationError("matrix must not be empty")
        matrix.flags.writeable = False
        return matrix.view(cls)

    def copy(self, order: Literal["K", "A", "C", "F"] | None = None) -> Matrix:
        """Return an owned copy that retains the Matrix type."""
        copied = np.asarray(self, dtype=float).copy(order=order)
        return cast(Matrix, copied.view(Matrix))

    def validate(self, name: str = "matrix") -> Matrix:
        """Validate finiteness, symmetry, and positive definiteness in place."""
        if not np.all(np.isfinite(self)):
            raise ValidationError(f"{name} must contain only finite values")
        if not np.allclose(self, self.T, rtol=1e-10, atol=1e-12):
            raise ValidationError(f"{name} must be symmetric")
        try:
            eigenvalues = np.linalg.eigvalsh(self)
        except np.linalg.LinAlgError as exc:
            raise ValidationError(f"{name} could not be factorised") from exc
        if float(np.min(eigenvalues)) <= 0.0:
            raise ValidationError(f"{name} must be positive definite")
        return self


__all__ = ["Matrix", "Vector"]
