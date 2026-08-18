"""Moment utilities for skew-t quadratic forms.

Formulas are sourced from Kim and Mallick (2003), Theorem 2 and Theorem 3,
combined with algebraic expansion of the paper's Eq. (Section 2.4).
"""

import math

import numpy as np

from oop.types import FloatArray


def compute_c_scalar(nu: float) -> float:
    """Computes c = sqrt(nu/pi) * Gamma((nu-1)/2) / Gamma(nu/2)."""
    if nu <= 1.0:
        raise ValueError("nu must be > 1 for c to exist")
    return math.sqrt(nu / math.pi) * math.gamma((nu - 1.0) / 2.0) / math.gamma(nu / 2.0)


def compute_h_vector(sigma: FloatArray, omega: FloatArray) -> FloatArray:
    """Computes h = Sigma*omega / sqrt(1 + omega^T Sigma omega)."""
    denom = math.sqrt(1.0 + float(omega.T @ sigma @ omega))
    return (sigma @ omega) / denom


def compute_q_vector(gamma_tensor: FloatArray, h_vector: FloatArray) -> FloatArray:
    """Computes q_m = h^T Gamma^[m] h for each instrument m."""
    instrument_count = gamma_tensor.shape[0]
    values = np.zeros(instrument_count, dtype=float)
    for index in range(instrument_count):
        values[index] = float(h_vector.T @ gamma_tensor[index] @ h_vector)
    return values


def compute_h_matrix(
    d_matrix: FloatArray,
    b_matrix: FloatArray,
    sigma: FloatArray,
    gamma_tensor: FloatArray,
    h_vector: FloatArray,
) -> FloatArray:
    """Computes H = (D + B^T)^T Sigma [Gamma^[1]h, ..., Gamma^[M]h]."""
    instrument_count = gamma_tensor.shape[0]
    third_derivative_column_stack = np.column_stack(
        [gamma_tensor[index] @ h_vector for index in range(instrument_count)]
    )
    return (d_matrix + b_matrix.T).T @ sigma @ third_derivative_column_stack


def compute_e_matrix(
    d_matrix: FloatArray,
    b_matrix: FloatArray,
    sigma: FloatArray,
    gamma_tensor: FloatArray,
    h_vector: FloatArray,
) -> FloatArray:
    """Computes E = H^T from bilinear expansion symmetry.

    Derived from x^T (D+B^T)^T Sigma Gamma(x) h and Q symmetrization in Eq. (3).
    """
    h_matrix = compute_h_matrix(d_matrix, b_matrix, sigma, gamma_tensor, h_vector)
    return h_matrix.T
