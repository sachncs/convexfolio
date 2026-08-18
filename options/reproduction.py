"""Paper-faithful algebraic constructions for Section 2.4."""

import numpy as np

from options.moments import compute_c_scalar
from options.moments import compute_e_matrix
from options.moments import compute_h_matrix
from options.moments import compute_h_vector
from options.moments import compute_q_vector
from options.types import FloatArray


def greeks(
    x: FloatArray,
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative_tensor: FloatArray,
) -> tuple[float, FloatArray, FloatArray]:
    """Computes theta, delta, gamma for a portfolio of options."""
    theta_value = float(price_drift.T @ x)
    delta_vector = delta_matrix @ x
    gamma_matrix = np.einsum("m,mij->ij", x, third_derivative_tensor)
    return theta_value, delta_vector, gamma_matrix


def portfolio_variance(
    gamma_matrix: FloatArray,
    delta_vector: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    c_coefficient: float,
    h_vector: FloatArray,
) -> float:
    """Direct scalar variance formula from Section 2.4."""
    auxiliary_vector = gamma_matrix @ expected_payoff + delta_vector
    term1 = (degrees_of_freedom**2 / (2.0 * (degrees_of_freedom - 2.0) * (degrees_of_freedom - 4.0))) * np.trace(
        (gamma_matrix @ covariance) @ (gamma_matrix @ covariance)
    )
    term2 = (degrees_of_freedom**2 / (2.0 * (degrees_of_freedom - 2.0) ** 2 * (degrees_of_freedom - 4.0))) * (
        np.trace(gamma_matrix @ covariance) ** 2
    )
    term3 = (degrees_of_freedom / (degrees_of_freedom - 2.0)) * float(
        auxiliary_vector.T @ covariance @ auxiliary_vector
    )
    term4 = (2.0 * c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * float(
        auxiliary_vector.T @ covariance @ gamma_matrix @ h_vector
    )
    term5 = (c_coefficient * degrees_of_freedom / ((degrees_of_freedom - 2.0) * (degrees_of_freedom - 3.0))) * float(
        auxiliary_vector.T @ h_vector
    ) * float(np.trace(gamma_matrix @ covariance))
    term6 = -(c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * float(
        auxiliary_vector.T @ h_vector
    ) * float(h_vector.T @ gamma_matrix @ h_vector)
    term7 = -(c_coefficient**2) * (float(auxiliary_vector.T @ h_vector) ** 2)
    return float(term1 + term2 + term3 + term4 + term5 + term6 + term7)


def linearize(
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative_tensor: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    skewness: FloatArray,
    time_increment: float,
) -> tuple[FloatArray, FloatArray]:
    """Builds u and Q using determined c,h,q,H,E definitions."""
    instrument_count = third_derivative_tensor.shape[0]
    c_coefficient = compute_c_scalar(degrees_of_freedom)
    h_vector = compute_h_vector(sigma=covariance, omega=skewness)

    pricing_vector = np.array(
        [
            np.trace(third_derivative_tensor[idx] @ covariance)
            for idx in range(instrument_count)
        ],
        dtype=float,
    )
    budget_matrix = np.vstack(
        [expected_payoff.T @ third_derivative_tensor[idx] for idx in range(instrument_count)]
    )
    xi_intercept = np.array(
        [
            0.5 * float(expected_payoff.T @ third_derivative_tensor[idx] @ expected_payoff)
            for idx in range(instrument_count)
        ],
        dtype=float,
    )

    zeta_intercept = (
        time_increment * price_drift
        + delta_matrix.T @ expected_payoff
        + (degrees_of_freedom / (2.0 * (degrees_of_freedom - 2.0))) * pricing_vector
        + xi_intercept
    )
    dual_residual = (
        zeta_intercept
        + c_coefficient * budget_matrix @ h_vector
        + c_coefficient * delta_matrix.T @ h_vector
    )

    residual_matrix = np.zeros((instrument_count, instrument_count), dtype=float)
    for i in range(instrument_count):
        for j in range(instrument_count):
            residual_matrix[i, j] = float(
                np.trace(
                    third_derivative_tensor[i]
                    @ covariance
                    @ third_derivative_tensor[j]
                    @ covariance
                )
            )

    uncertainty_matrix = (
        (2.0 * degrees_of_freedom / (degrees_of_freedom - 2.0))
        * ((delta_matrix.T + budget_matrix) @ covariance @ (delta_matrix.T + budget_matrix).T)
        + (degrees_of_freedom**2 / ((degrees_of_freedom - 2.0) * (degrees_of_freedom - 4.0)))
        * residual_matrix
        + (
            degrees_of_freedom**2
            / ((degrees_of_freedom - 2.0) ** 2 * (degrees_of_freedom - 4.0))
        )
        * np.outer(pricing_vector, pricing_vector)
    )

    q_vector = compute_q_vector(
        gamma_tensor=third_derivative_tensor, h_vector=h_vector
    )
    h_matrix = compute_h_matrix(
        d_matrix=delta_matrix,
        b_matrix=budget_matrix,
        sigma=covariance,
        gamma_tensor=third_derivative_tensor,
        h_vector=h_vector,
    )
    e_matrix = compute_e_matrix(
        d_matrix=delta_matrix,
        b_matrix=budget_matrix,
        sigma=covariance,
        gamma_tensor=third_derivative_tensor,
        h_vector=h_vector,
    )

    delta_plus_budget_transpose = budget_matrix + delta_matrix.T
    q_symmetric_part = (
        uncertainty_matrix
        + (4.0 * c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * (h_matrix + e_matrix)
        + (2.0 * c_coefficient * degrees_of_freedom / ((degrees_of_freedom - 2.0) * (degrees_of_freedom - 3.0))) * np.outer(
            delta_plus_budget_transpose @ h_vector, pricing_vector
        )
        - (2.0 * c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * np.outer(
            delta_plus_budget_transpose @ h_vector, q_vector
        )
        - 2.0 * c_coefficient**2 * np.outer(
            delta_plus_budget_transpose @ h_vector,
            delta_plus_budget_transpose @ h_vector,
        )
    )

    precision_matrix = 0.5 * (q_symmetric_part + q_symmetric_part.T)
    return dual_residual, precision_matrix


def reconstruct(
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative_tensor: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    skewness: FloatArray,
) -> FloatArray:
    """Reconstructs Q from direct variance formula evaluations.

    Since Var[ΔV(x)] is quadratic in x, this recovers the exact symmetric Q.
    """
    instrument_count = third_derivative_tensor.shape[0]
    c_coefficient = compute_c_scalar(degrees_of_freedom)
    h_vector = compute_h_vector(sigma=covariance, omega=skewness)
    precision_matrix = np.zeros((instrument_count, instrument_count), dtype=float)

    def variance_at(x_vec: FloatArray) -> float:
        _, delta_vec, gamma_mat = greeks(
            x=x_vec,
            price_drift=price_drift,
            delta_matrix=delta_matrix,
            third_derivative_tensor=third_derivative_tensor,
        )
        return portfolio_variance(
            gamma_matrix=gamma_mat,
            delta_vector=delta_vec,
            expected_payoff=expected_payoff,
            covariance=covariance,
            degrees_of_freedom=degrees_of_freedom,
            c_coefficient=c_coefficient,
            h_vector=h_vector,
        )

    basis = np.eye(instrument_count)
    for i in range(instrument_count):
        precision_matrix[i, i] = 2.0 * variance_at(basis[i])
    for i in range(instrument_count):
        for j in range(i + 1, instrument_count):
            mixed_variance = variance_at(basis[i] + basis[j])
            precision_matrix[i, j] = (
                mixed_variance
                - 0.5 * precision_matrix[i, i]
                - 0.5 * precision_matrix[j, j]
            )
            precision_matrix[j, i] = precision_matrix[i, j]
    return precision_matrix
