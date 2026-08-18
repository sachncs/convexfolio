"""Optimization problems P1, P2, P3 from Section 3."""

import math

import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from options.risk import cfvar2
from options.risk import cfvar3
from options.types import FloatArray


def solve_variance_minimization(v: FloatArray, q_matrix: FloatArray) -> FloatArray:
    """Closed form Eq. (4) for P1."""
    precision_inverse = np.linalg.inv(q_matrix)
    denominator = float(v.T @ precision_inverse @ v)
    return (precision_inverse @ v) / denominator


def loss(epsilon: float, coeff_a: float, coeff_b: float, coeff_c: float) -> float:
    """Quadratic variance term at epsilon for the Lagrange multiplier search."""
    return coeff_a * epsilon * epsilon + coeff_b * epsilon + coeff_c


def score(
    epsilon: float, coeff_a: float, coeff_b: float, coeff_c: float, z_score: float
) -> float:
    """CFVaR2 upper bound at epsilon; returns inf when variance is non-positive."""
    term = loss(epsilon, coeff_a, coeff_b, coeff_c)
    if term <= 0.0:
        return float("inf")
    return -epsilon - z_score * math.sqrt(term)


def compute_epsilon_star(
    alpha: float, u: FloatArray, v: FloatArray, q_matrix: FloatArray
) -> float:
    """Computes epsilon_star using Appendix B derivation.

    Preferred path: closed-form roots from Appendix B.
    Deterministic fallback: bounded numerical minimization if root conditions fail.
    """
    z_score = float(norm.ppf(alpha))
    if not np.isfinite(z_score):
        raise ValueError("Could not compute normal quantile")

    precision_inverse = np.linalg.inv(q_matrix)
    constraint_matrix = np.vstack([u.T, v.T])
    projection = precision_inverse @ constraint_matrix.T @ np.linalg.inv(
        constraint_matrix @ precision_inverse @ constraint_matrix.T
    )

    loss_gradient = projection[:, 0]
    constraint_gradient = projection[:, 1]
    coeff_a = 0.5 * float(loss_gradient.T @ q_matrix @ loss_gradient)
    coeff_b = float(constraint_gradient.T @ q_matrix @ loss_gradient)
    coeff_c = 0.5 * float(constraint_gradient.T @ q_matrix @ constraint_gradient)

    score_a = 4.0 * coeff_a * coeff_a * z_score * z_score - 4.0 * coeff_a
    score_b = 4.0 * coeff_a * coeff_b * z_score * z_score - 4.0 * coeff_b
    score_c = coeff_b * coeff_b * z_score * z_score - 4.0 * coeff_c
    discriminant = score_b * score_b - 4.0 * score_a * score_c

    candidate_solutions = []
    if abs(score_a) > 1e-12 and discriminant >= 0.0:
        epsilon_plus = (-score_b + math.sqrt(discriminant)) / (2.0 * score_a)
        epsilon_minus = (-score_b - math.sqrt(discriminant)) / (2.0 * score_a)
        if 2.0 * coeff_a * epsilon_plus + coeff_b > 0.0 and loss(epsilon_plus, coeff_a, coeff_b, coeff_c) > 0.0:
            candidate_solutions.append(epsilon_plus)
        if 2.0 * coeff_a * epsilon_minus + coeff_b > 0.0 and loss(epsilon_minus, coeff_a, coeff_b, coeff_c) > 0.0:
            candidate_solutions.append(epsilon_minus)

    if candidate_solutions:
        return min(
            candidate_solutions,
            key=lambda eps: score(eps, coeff_a, coeff_b, coeff_c, z_score),
        )

    search_radius = 1e3
    result = minimize_scalar(
        lambda eps: score(eps, coeff_a, coeff_b, coeff_c, z_score),
        method="bounded",
        bounds=(-search_radius, search_radius),
    )
    if not result.success or not np.isfinite(result.fun):
        raise ValueError("Could not compute epsilon_star via closed-form or fallback solver")
    return float(result.x)


def solve_cfvar2_closed_form(
    q_matrix: FloatArray,
    u: FloatArray,
    v: FloatArray,
    alpha: float,
) -> FloatArray:
    """Eq. (5)-(6) for P2 with determined epsilon_star."""
    optimal_epsilon = compute_epsilon_star(
        alpha=alpha, u=u, v=v, q_matrix=q_matrix
    )
    precision_inverse = np.linalg.inv(q_matrix)
    constraint_matrix = np.vstack([u.T, v.T])
    dual_variable = np.array([optimal_epsilon, 1.0], dtype=float)
    left_factor = precision_inverse @ constraint_matrix.T
    right_factor = (
        np.linalg.inv(constraint_matrix @ precision_inverse @ constraint_matrix.T)
        @ dual_variable
    )
    return left_factor @ right_factor


def solve_cfvar3_numerical(
    v: FloatArray,
    initial_x: FloatArray,
    objective_callable,
) -> FloatArray:
    """Numerical solution for P3 with equality constraint x^T v = 1."""
    constraints = [{"type": "eq", "fun": lambda x: float(np.dot(x, v) - 1.0)}]
    result = minimize(
        objective_callable, x0=initial_x, method="SLSQP", constraints=constraints
    )
    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")
    return np.asarray(result.x, dtype=float)


def cfvar3_objective(
    alpha: float, u: FloatArray, q_matrix: FloatArray, kappa3_callback
):
    """Factory for numerical P3 objective."""

    def objective(x: FloatArray) -> float:
        return cfvar3(alpha, u, q_matrix, np.asarray(x, dtype=float), float(kappa3_callback(x)))

    return objective


def quality_score(
    alpha: float, u: FloatArray, v: FloatArray, q_matrix: FloatArray
) -> float:
    """Returns CFVaR2 value at closed-form solution for sanity checks."""
    closed_form_weights = solve_cfvar2_closed_form(
        q_matrix=q_matrix, u=u, v=v, alpha=alpha
    )
    return cfvar2(
        alpha=alpha, u=u, q_matrix=q_matrix, x=closed_form_weights
    )
