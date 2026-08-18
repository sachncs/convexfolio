"""Math operations for the optimal option portfolio optimizer.

All numerical routines live here: moment computations, risk primitives,
optimization, and paper-faithful algebraic constructions from Section 2.4.
"""

import math

import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from options.types import FloatArray


def compute(degrees_of_freedom: float) -> float:
    """Compute the skew-t coefficient c = sqrt(nu/pi) * Gamma((nu-1)/2) / Gamma(nu/2)."""
    if degrees_of_freedom <= 1.0:
        raise ValueError("degrees_of_freedom must be > 1 for coeff to exist")
    return math.sqrt(degrees_of_freedom / math.pi) * math.gamma((degrees_of_freedom - 1.0) / 2.0) / math.gamma(degrees_of_freedom / 2.0)


def linear(covariance: FloatArray, skewness: FloatArray) -> FloatArray:
    """Compute the h vector: Sigma*omega / sqrt(1 + omega^T Sigma omega)."""
    denominator = math.sqrt(1.0 + float(skewness.T @ covariance @ skewness))
    return (covariance @ skewness) / denominator


def curvature(third_derivative: FloatArray, h: FloatArray) -> FloatArray:
    """Compute the q vector: h^T Gamma^[m] h for each instrument m."""
    instrument_count = third_derivative.shape[0]
    values = np.zeros(instrument_count, dtype=float)
    for index in range(instrument_count):
        values[index] = float(h.T @ third_derivative[index] @ h)
    return values


class Curvature:
    """Deterministic q vector: h^T Gamma^[m] h for each instrument m.

    Standard, deterministic behaviour. Same ``third_derivative`` and
    ``h`` always produce the same vector.
    """

    def __init__(self, third_derivative: FloatArray, h: FloatArray) -> None:
        self.third_derivative = third_derivative
        self.h = h
        self.values = curvature(third_derivative, h)

    @property
    def vector(self) -> FloatArray:
        return self.values


def bilinear(
    delta_matrix: FloatArray,
    budget_matrix: FloatArray,
    covariance: FloatArray,
    third_derivative: FloatArray,
    h: FloatArray,
) -> FloatArray:
    """Compute the hmatrix: (D + B^T)^T Sigma [Gamma^[1]h, ..., Gamma^[M]h]."""
    instrument_count = third_derivative.shape[0]
    gammacolumns = np.column_stack(
        [third_derivative[index] @ h for index in range(instrument_count)]
    )
    return (delta_matrix + budget_matrix.T).T @ covariance @ gammacolumns


class Bilinear:
    """Deterministic hmatrix: (D + B^T)^T Sigma [Gamma^[1]h, ..., Gamma^[M]h].

    Standard, deterministic behaviour. Same inputs always produce the same matrix.
    """

    def __init__(
        self,
        delta_matrix: FloatArray,
        budget_matrix: FloatArray,
        covariance: FloatArray,
        third_derivative: FloatArray,
        h: FloatArray,
    ) -> None:
        self.delta_matrix = delta_matrix
        self.budget_matrix = budget_matrix
        self.covariance = covariance
        self.third_derivative = third_derivative
        self.h = h
        self.matrix = bilinear(
            delta_matrix,
            budget_matrix,
            covariance,
            third_derivative,
            h,
        )

    @property
    def values(self) -> FloatArray:
        return self.matrix


def cross(
    delta_matrix: FloatArray,
    budget_matrix: FloatArray,
    covariance: FloatArray,
    third_derivative: FloatArray,
    h: FloatArray,
) -> FloatArray:
    """Compute the h matrix: (D + B^T)^T Sigma [Gamma^[1]h, ..., Gamma^[M]h]."""
    instrument_count = third_derivative.shape[0]
    gammacolumns = np.column_stack(
        [third_derivative[index] @ h for index in range(instrument_count)]
    )
    return (delta_matrix + budget_matrix.T).T @ covariance @ gammacolumns


def cross(
    delta_matrix: FloatArray,
    budget_matrix: FloatArray,
    covariance: FloatArray,
    third_derivative: FloatArray,
    h: FloatArray,
) -> FloatArray:
    """Compute the e matrix: H^T from bilinear expansion symmetry."""
    hmatrix = bilinear(
        delta_matrix, budget_matrix, covariance, third_derivative, h
    )
    return hmatrix.T


class Cross:
    """Deterministic e matrix: H^T from bilinear expansion symmetry.

    Standard, deterministic behaviour. Same inputs always produce the same matrix.
    """

    def __init__(
        self,
        delta_matrix: FloatArray,
        budget_matrix: FloatArray,
        covariance: FloatArray,
        third_derivative: FloatArray,
        h: FloatArray,
    ) -> None:
        self.delta_matrix = delta_matrix
        self.budget_matrix = budget_matrix
        self.covariance = covariance
        self.third_derivative = third_derivative
        self.h = h
        self.matrix = cross(
            delta_matrix,
            budget_matrix,
            covariance,
            third_derivative,
            h,
        )

    @property
    def values(self) -> FloatArray:
        return self.matrix


def shapes(expected_payoff: FloatArray, precision_matrix: FloatArray, weights: FloatArray) -> None:
    """Validate tensor shapes used by risk and optimization primitives."""
    if expected_payoff.ndim != 1 or weights.ndim != 1:
        raise ValueError("expected_payoff and weights must be 1D vectors")
    if precision_matrix.ndim != 2 or precision_matrix.shape[0] != precision_matrix.shape[1]:
        raise ValueError("precision_matrix must be square")
    if precision_matrix.shape[0] != weights.shape[0] or expected_payoff.shape[0] != weights.shape[0]:
        raise ValueError("Incompatible vector/matrix dimensions")


def expect(expected_payoff: FloatArray, weights: FloatArray) -> float:
    """E[ΔV(x)] = u^T x."""
    return float(np.dot(expected_payoff, weights))


def quadratic(precision_matrix: FloatArray, weights: FloatArray) -> float:
    """Var[ΔV(x)] = 0.5 x^T Q x."""
    return float(0.5 * weights.T @ precision_matrix @ weights)


def third_order_cumulant(
    weights: FloatArray,
    degrees_of_freedom: float,
    pricing_vector: FloatArray,
    residual_matrix: FloatArray,
    delta_matrix: FloatArray,
    budget_matrix: FloatArray,
    covariance: FloatArray,
    tau: FloatArray,
) -> float:
    """Eq. (S2.Ex24-S2.Ex26): third central moment approximation."""
    linear_pricing_term = float(weights.T @ pricing_vector)
    quadratic_pricing_term = float(weights.T @ residual_matrix @ weights)
    volatility_contribution_term = float(
        weights.T @ (delta_matrix.T + budget_matrix).T @ covariance @ (delta_matrix + budget_matrix.T) @ weights
    )
    fourth_order_term = float(np.einsum("ijk,i,j,k->", tau, weights, weights, weights))

    term1 = (
        2.0
        * degrees_of_freedom**3
        / ((degrees_of_freedom - 2.0) ** 3 * (degrees_of_freedom - 4.0) * (degrees_of_freedom - 6.0))
        * linear_pricing_term**3
    )
    term2 = (
        3.0
        * degrees_of_freedom**3
        / ((degrees_of_freedom - 2.0) ** 2 * (degrees_of_freedom - 4.0) * (degrees_of_freedom - 6.0))
        * linear_pricing_term
        * quadratic_pricing_term
    )
    term3 = (
        3.0
        * degrees_of_freedom**2
        / ((degrees_of_freedom - 2.0) ** 2 * (degrees_of_freedom - 4.0))
        * linear_pricing_term
        * volatility_contribution_term
    )
    return float(term1 + term2 + term3 + fourth_order_term)


def second_order_risk(
    alpha: float,
    expected_payoff: FloatArray,
    precision_matrix: FloatArray,
    weights: FloatArray,
) -> float:
    """Eq. (S2.Ex22)."""
    shapes(expected_payoff, precision_matrix, weights)
    z_alpha = norm.ppf(alpha)
    variance_value = quadratic(precision_matrix, weights)
    return float(
        -expect(expected_payoff, weights) - z_alpha * np.sqrt(variance_value)
    )


def third_order_risk(
    alpha: float,
    expected_payoff: FloatArray,
    precision_matrix: FloatArray,
    weights: FloatArray,
    third_order_cumulant: float,
) -> float:
    """Eq. (S2.Ex23)."""
    shapes(expected_payoff, precision_matrix, weights)
    z_alpha = norm.ppf(alpha)
    variance_value = quadratic(precision_matrix, weights)
    skewness_correction = (
        (z_alpha**2 - 1.0) / 6.0 * (third_order_cumulant / variance_value)
    )
    return float(
        -expect(expected_payoff, weights)
        - z_alpha * np.sqrt(variance_value)
        - skewness_correction
    )


def minimize_variance(cost_vector: FloatArray, precision_matrix: FloatArray) -> FloatArray:
    """Closed form Eq. (4) for P1."""
    precision_inverse = np.linalg.inv(precision_matrix)
    denominator = float(cost_vector.T @ precision_inverse @ cost_vector)
    return (precision_inverse @ cost_vector) / denominator


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


def optimal_epsilon(
    alpha: float, expected_payoff: FloatArray, cost_vector: FloatArray, precision_matrix: FloatArray
) -> float:
    """Computes epsilon_star using Appendix B derivation.

    Preferred path: closed-form roots from Appendix B.
    Deterministic fallback: bounded numerical minimization if root conditions fail.
    """
    z_score = float(norm.ppf(alpha))
    if not np.isfinite(z_score):
        raise ValueError("Could not compute normal quantile")

    precision_inverse = np.linalg.inv(precision_matrix)
    constraint_matrix = np.vstack([expected_payoff.T, cost_vector.T])
    projection = precision_inverse @ constraint_matrix.T @ np.linalg.inv(
        constraint_matrix @ precision_inverse @ constraint_matrix.T
    )

    loss_gradient = projection[:, 0]
    constraint_gradient = projection[:, 1]
    coeff_a = 0.5 * float(loss_gradient.T @ precision_matrix @ loss_gradient)
    coeff_b = float(constraint_gradient.T @ precision_matrix @ loss_gradient)
    coeff_c = 0.5 * float(constraint_gradient.T @ precision_matrix @ constraint_gradient)

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
    precision_matrix: FloatArray,
    expected_payoff: FloatArray,
    cost_vector: FloatArray,
    alpha: float,
) -> FloatArray:
    """Eq. (5)-(6) for P2 with determined epsilon_star."""
    optimal_epsilon_value = optimal_epsilon(
        alpha=alpha,
        expected_payoff=expected_payoff,
        cost_vector=cost_vector,
        precision_matrix=precision_matrix,
    )
    precision_inverse = np.linalg.inv(precision_matrix)
    constraint_matrix = np.vstack([expected_payoff.T, cost_vector.T])
    dual_variable = np.array([optimal_epsilon_value, 1.0], dtype=float)
    left_factor = precision_inverse @ constraint_matrix.T
    right_factor = (
        np.linalg.inv(constraint_matrix @ precision_inverse @ constraint_matrix.T)
        @ dual_variable
    )
    return left_factor @ right_factor


def solve_cfvar3_numerical(
    cost_vector: FloatArray,
    initial_weights: FloatArray,
    objective_callable,
) -> FloatArray:
    """Numerical solution for P3 with equality constraint x^T v = 1."""
    constraints = [{"type": "eq", "fun": lambda x: float(np.dot(x, cost_vector) - 1.0)}]
    result = minimize(
        objective_callable, x0=initial_weights, method="SLSQP", constraints=constraints
    )
    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")
    return np.asarray(result.x, dtype=float)


def third_order_objective(
    weights: FloatArray,
    alpha: float,
    expected_payoff: FloatArray,
    precision_matrix: FloatArray,
    kappa3_callback,
) -> float:
    """Body of the third-order Objective: same pattern as second_order_risk."""
    return third_order_risk(
        alpha,
        expected_payoff,
        precision_matrix,
        np.asarray(weights, dtype=float),
        float(kappa3_callback(weights)),
    )


class Objective:
    """Deterministic callable wrapper around any scalar objective function.

    The objective body is a callable of the form ``f(weights=..., **parameters)``.
    Parameters are captured at construction; the instance binds them and exposes
    ``__call__(weights)``. Same parameters and same weights always produce the
    same output. Standard, deterministic behaviour; no polymorphism.
    """

    def __init__(self, function, **parameters) -> None:
        self.function = function
        self.parameters = parameters

    def __call__(self, weights: FloatArray) -> float:
        return self.function(weights=weights, **self.parameters)


class Risk:
    """Risk measure facade. Standard deterministic computation of risk numbers.

    Holds a fixed ``alpha``, ``expected_payoff``, and ``precision_matrix`` and
    delegates evaluation to ``Objective`` instances.
    """

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        precision_matrix: FloatArray,
    ) -> None:
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.precision_matrix = precision_matrix
        self.second_order = Objective(
            second_order_risk,
            alpha=alpha,
            expected_payoff=expected_payoff,
            precision_matrix=precision_matrix,
        )

    def second(self, weights: FloatArray) -> float:
        return self.second_order(weights)

    def third(
        self, weights: FloatArray, kappa3_callback
    ) -> float:
        return Objective(
            third_order_objective,
            alpha=self.alpha,
            expected_payoff=self.expected_payoff,
            precision_matrix=self.precision_matrix,
            kappa3_callback=kappa3_callback,
        )(weights)


def quality_score(
    alpha: float,
    expected_payoff: FloatArray,
    cost_vector: FloatArray,
    precision_matrix: FloatArray,
) -> float:
    """Returns CFVaR2 value at closed-form solution for sanity checks."""
    closed_form_weights = solve_cfvar2_closed_form(
        precision_matrix=precision_matrix,
        expected_payoff=expected_payoff,
        cost_vector=cost_vector,
        alpha=alpha,
    )
    return second_order_risk(
        alpha=alpha,
        expected_payoff=expected_payoff,
        precision_matrix=precision_matrix,
        weights=closed_form_weights,
    )


def greeks(
    weights: FloatArray,
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative: FloatArray,
) -> tuple[float, FloatArray, FloatArray]:
    """Compute theta, delta, gamma for a portfolio of options."""
    theta_value = float(price_drift.T @ weights)
    delta_vector = delta_matrix @ weights
    gamma_matrix = np.einsum("m,mij->ij", weights, third_derivative)
    return theta_value, delta_vector, gamma_matrix


def portfolio_variance(
    gamma_matrix: FloatArray,
    delta_vector: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    c_coefficient: float,
    h: FloatArray,
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
        auxiliary_vector.T @ covariance @ gamma_matrix @ h
    )
    term5 = (c_coefficient * degrees_of_freedom / ((degrees_of_freedom - 2.0) * (degrees_of_freedom - 3.0))) * float(
        auxiliary_vector.T @ h
    ) * float(np.trace(gamma_matrix @ covariance))
    term6 = -(c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * float(
        auxiliary_vector.T @ h
    ) * float(h.T @ gamma_matrix @ h)
    term7 = -(c_coefficient**2) * (float(auxiliary_vector.T @ h) ** 2)
    return float(term1 + term2 + term3 + term4 + term5 + term6 + term7)


def linearize(
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    skewness: FloatArray,
    time_increment: float,
) -> tuple[FloatArray, FloatArray]:
    """Build linearized expected return and precision matrix for the section-2.4 problem."""
    instrument_count = third_derivative.shape[0]
    c_coefficient = compute(degrees_of_freedom)
    h = linear(covariance, skewness)

    pricing_vector = np.array(
        [
            np.trace(third_derivative[idx] @ covariance)
            for idx in range(instrument_count)
        ],
        dtype=float,
    )
    budget_matrix = np.vstack(
        [expected_payoff.T @ third_derivative[idx] for idx in range(instrument_count)]
    )
    xi_intercept = np.array(
        [
            0.5 * float(expected_payoff.T @ third_derivative[idx] @ expected_payoff)
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
        + c_coefficient * budget_matrix @ h
        + c_coefficient * delta_matrix.T @ h
    )

    residual_matrix = np.zeros((instrument_count, instrument_count), dtype=float)
    for i in range(instrument_count):
        for j in range(instrument_count):
            residual_matrix[i, j] = float(
                np.trace(
                    third_derivative[i]
                    @ covariance
                    @ third_derivative[j]
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

    q = curvature(
        third_derivative=third_derivative, h=h
    )
    hmatrix = bilinear(
        delta_matrix=delta_matrix,
        budget_matrix=budget_matrix,
        covariance=covariance,
        third_derivative=third_derivative,
        h=h,
    )
    e = cross(
        delta_matrix=delta_matrix,
        budget_matrix=budget_matrix,
        covariance=covariance,
        third_derivative=third_derivative,
        h=h,
    )

    delta_plus_budget_transpose = budget_matrix + delta_matrix.T
    q_symmetric_part = (
        uncertainty_matrix
        + (4.0 * c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * (hmatrix + e)
        + (2.0 * c_coefficient * degrees_of_freedom / ((degrees_of_freedom - 2.0) * (degrees_of_freedom - 3.0))) * np.outer(
            delta_plus_budget_transpose @ h, pricing_vector
        )
        - (2.0 * c_coefficient * degrees_of_freedom / (degrees_of_freedom - 3.0)) * np.outer(
            delta_plus_budget_transpose @ h, q
        )
        - 2.0 * c_coefficient**2 * np.outer(
            delta_plus_budget_transpose @ h,
            delta_plus_budget_transpose @ h,
        )
    )

    precision_matrix = 0.5 * (q_symmetric_part + q_symmetric_part.T)
    return dual_residual, precision_matrix


def reconstruct(
    price_drift: FloatArray,
    delta_matrix: FloatArray,
    third_derivative: FloatArray,
    expected_payoff: FloatArray,
    covariance: FloatArray,
    degrees_of_freedom: float,
    skewness: FloatArray,
) -> FloatArray:
    """Reconstruct Q from portfolio variance evaluations.

    Since Var[ΔV(x)] is quadratic in x, this recovers the exact symmetric Q.
    """
    instrument_count = third_derivative.shape[0]
    c_coefficient = compute(degrees_of_freedom)
    h = linear(covariance, skewness)
    precision_matrix = np.zeros((instrument_count, instrument_count), dtype=float)

    def variance_at(xvec: FloatArray) -> float:
        _, delta_vec, gamma_mat = greeks(
            weights=xvec,
            price_drift=price_drift,
            delta_matrix=delta_matrix,
            third_derivative=third_derivative,
        )
        return portfolio_variance(
            gamma_matrix=gamma_mat,
            delta_vector=delta_vec,
            expected_payoff=expected_payoff,
            covariance=covariance,
            degrees_of_freedom=degrees_of_freedom,
            c_coefficient=c_coefficient,
            h=h,
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
