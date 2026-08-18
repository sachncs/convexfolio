"""Risk and moment formulas from Sections 2.4-2.5."""

import numpy as np
from scipy.stats import norm

from options.types import FloatArray


def validate_shapes(
    u: FloatArray, q_matrix: FloatArray, x: FloatArray
) -> None:
    """Defensive checks on key tensor shapes."""
    if u.ndim != 1 or x.ndim != 1:
        raise ValueError("u and x must be 1D vectors")
    if q_matrix.ndim != 2 or q_matrix.shape[0] != q_matrix.shape[1]:
        raise ValueError("Q must be square")
    if q_matrix.shape[0] != x.shape[0] or u.shape[0] != x.shape[0]:
        raise ValueError("Incompatible vector/matrix dimensions")


def expectation_linear(u: FloatArray, x: FloatArray) -> float:
    """Eq. (3): E[ΔV(x)] = u^T x."""
    return float(np.dot(u, x))


def variance_quadratic(q_matrix: FloatArray, x: FloatArray) -> float:
    """Eq. (3): Var[ΔV(x)] = 0.5 x^T Q x."""
    return float(0.5 * x.T @ q_matrix @ x)


def kappa3(
    x: FloatArray,
    nu: float,
    p_vec: FloatArray,
    r_matrix: FloatArray,
    d_matrix: FloatArray,
    b_matrix: FloatArray,
    sigma_matrix: FloatArray,
    tau_tensor: FloatArray,
) -> float:
    """Eq. (S2.Ex24-S2.Ex26) third central moment approximation."""
    linear_pricing_term = float(x.T @ p_vec)
    quadratic_pricing_term = float(x.T @ r_matrix @ x)
    volatility_contribution_term = float(
        x.T @ (d_matrix.T + b_matrix).T @ sigma_matrix @ (d_matrix + b_matrix.T) @ x
    )
    fourth_order_term = float(np.einsum("ijk,i,j,k->", tau_tensor, x, x, x))

    term1 = (
        2.0
        * nu**3
        / ((nu - 2.0) ** 3 * (nu - 4.0) * (nu - 6.0))
        * linear_pricing_term**3
    )
    term2 = (
        3.0
        * nu**3
        / ((nu - 2.0) ** 2 * (nu - 4.0) * (nu - 6.0))
        * linear_pricing_term
        * quadratic_pricing_term
    )
    term3 = (
        3.0
        * nu**2
        / ((nu - 2.0) ** 2 * (nu - 4.0))
        * linear_pricing_term
        * volatility_contribution_term
    )
    return float(term1 + term2 + term3 + fourth_order_term)


def cfvar2(
    alpha: float, u: FloatArray, q_matrix: FloatArray, x: FloatArray
) -> float:
    """Eq. (S2.Ex22)."""
    validate_shapes(u, q_matrix, x)
    z_alpha = norm.ppf(alpha)
    variance_value = variance_quadratic(q_matrix, x)
    return float(
        -expectation_linear(u, x) - z_alpha * np.sqrt(variance_value)
    )


def cfvar3(
    alpha: float,
    u: FloatArray,
    q_matrix: FloatArray,
    x: FloatArray,
    third_order_cumulant: float,
) -> float:
    """Eq. (S2.Ex23)."""
    validate_shapes(u, q_matrix, x)
    z_alpha = norm.ppf(alpha)
    variance_value = variance_quadratic(q_matrix, x)
    skewness_correction = (
        (z_alpha**2 - 1.0) / 6.0 * (third_order_cumulant / variance_value)
    )
    return float(
        -expectation_linear(u, x)
        - z_alpha * np.sqrt(variance_value)
        - skewness_correction
    )
