"""Math operations for the optimal option portfolio optimizer.

Each numerical routine lives in a concrete class. Class instantiation captures
the deterministic inputs; ``.value`` (or named attribute) holds the result.
Polymorphic composition: ``Minimize(Variance(Q), c).value`` runs a closed-form
variance minimizer; ``CFVaR2nd(alpha, mean, Q, x).value`` evaluates the second
order risk number.
"""

import math

import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from scipy.stats import norm

from options.types import FloatArray


def shapes(expected_payoff: FloatArray, precision_matrix: FloatArray, weights: FloatArray) -> None:
    """Validate tensor shapes used by risk and optimisation primitives."""
    if expected_payoff.ndim != 1 or weights.ndim != 1:
        raise ValueError("expected_payoff and weights must be 1D vectors")
    if precision_matrix.ndim != 2 or precision_matrix.shape[0] != precision_matrix.shape[1]:
        raise ValueError("precision_matrix must be square")
    if precision_matrix.shape[0] != weights.shape[0] or expected_payoff.shape[0] != weights.shape[0]:
        raise ValueError("Incompatible vector/matrix dimensions")


class Compute:
    """Skew-t coefficient c = sqrt(nu/pi) * Gamma((nu-1)/2) / Gamma(nu/2)."""

    def __init__(self, degrees_of_freedom: float) -> None:
        if degrees_of_freedom <= 1.0:
            raise ValueError("degrees_of_freedom must be > 1 for coeff to exist")
        self.degrees_of_freedom = degrees_of_freedom
        self.value = math.sqrt(degrees_of_freedom / math.pi) * math.gamma((degrees_of_freedom - 1.0) / 2.0) / math.gamma(degrees_of_freedom / 2.0)


class Linear:
    """h vector: Sigma*omega / sqrt(1 + omega^T Sigma omega)."""

    def __init__(self, covariance: FloatArray, skewness: FloatArray) -> None:
        self.covariance = covariance
        self.skewness = skewness
        denominator = math.sqrt(1.0 + float(skewness.T @ covariance @ skewness))
        self.value = (covariance @ skewness) / denominator


class Curvature:
    """q vector: h^T Gamma^[m] h for each instrument m."""

    def __init__(self, third_derivative: FloatArray, h: FloatArray) -> None:
        self.third_derivative = third_derivative
        self.h = h
        instrument_count = third_derivative.shape[0]
        values = np.zeros(instrument_count, dtype=float)
        for index in range(instrument_count):
            values[index] = float(h.T @ third_derivative[index] @ h)
        self.values = values


class Bilinear:
    """hmatrix: (D + B^T)^T Sigma [Gamma^[1]h, ..., Gamma^[M]h]."""

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
        instrument_count = third_derivative.shape[0]
        gammacolumns = np.column_stack(
            [third_derivative[index] @ h for index in range(instrument_count)]
        )
        self.matrix = (delta_matrix + budget_matrix.T).T @ covariance @ gammacolumns


class Cross:
    """e matrix: H^T from bilinear expansion symmetry."""

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
        self.matrix = Bilinear(
            delta_matrix, budget_matrix, covariance, third_derivative, h
        ).matrix.T


class Expect:
    """E[ΔV(x)] = u^T x."""

    def __init__(self, expected_payoff: FloatArray, weights: FloatArray) -> None:
        self.expected_payoff = expected_payoff
        self.weights = weights
        self.value = float(np.dot(expected_payoff, weights))


class Quadratic:
    """Var[ΔV(x)] = 0.5 x^T Q x."""

    def __init__(self, precision_matrix: FloatArray, weights: FloatArray) -> None:
        self.precision_matrix = precision_matrix
        self.weights = weights
        self.value = float(0.5 * weights.T @ precision_matrix @ weights)


class Variance:
    """Portfolio variance objective: x → 0.5 x^T Q x.

    Callable; pass ``weights`` to evaluate. Use ``Minimize(Variance(Q), v)`` to
    solve for the closed-form minimising weights.
    """

    def __init__(self, precision_matrix: FloatArray) -> None:
        self.precision_matrix = precision_matrix

    def __call__(self, weights: FloatArray) -> float:
        return Quadratic(self.precision_matrix, weights).value


class Cumulant:
    """Eq. (S2.Ex24-S2.Ex26): third central moment approximation."""

    def __init__(
        self,
        weights: FloatArray,
        degrees_of_freedom: float,
        pricing_vector: FloatArray,
        residual_matrix: FloatArray,
        delta_matrix: FloatArray,
        budget_matrix: FloatArray,
        covariance: FloatArray,
        tau: FloatArray,
    ) -> None:
        self.weights = weights
        self.degrees_of_freedom = degrees_of_freedom
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
        self.value = float(term1 + term2 + term3 + fourth_order_term)


class CFVaR2nd:
    """Eq. (S2.Ex22): second-order CFVaR risk number at given weights."""

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        precision_matrix: FloatArray,
        weights: FloatArray,
    ) -> None:
        shapes(expected_payoff, precision_matrix, weights)
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.precision_matrix = precision_matrix
        self.weights = weights
        z_alpha = norm.ppf(alpha)
        variance_value = Quadratic(precision_matrix, weights).value
        self.value = float(
            -Expect(expected_payoff, weights).value - z_alpha * np.sqrt(variance_value)
        )


class CFVaR3rd:
    """Eq. (S2.Ex23): third-order CFVaR risk number at given weights."""

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        precision_matrix: FloatArray,
        weights: FloatArray,
        cumulant: float,
    ) -> None:
        shapes(expected_payoff, precision_matrix, weights)
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.precision_matrix = precision_matrix
        self.weights = weights
        self.cumulant = cumulant
        z_alpha = norm.ppf(alpha)
        variance_value = Quadratic(precision_matrix, weights).value
        skewness_correction = (
            (z_alpha**2 - 1.0) / 6.0 * (cumulant / variance_value)
        )
        self.value = float(
            -Expect(expected_payoff, weights).value
            - z_alpha * np.sqrt(variance_value)
            - skewness_correction
        )


class Minimize:
    """Closed-form minimisation of a Variance objective under budget.

    Usage: ``Minimize(Variance(Q), c).value`` returns the weights
    minimising variance subject to ``c.T @ x == 1``.
    """

    def __init__(self, variance: Variance, cost_vector: FloatArray) -> None:
        self.variance = variance
        self.cost_vector = cost_vector
        precision_inverse = np.linalg.inv(variance.precision_matrix)
        denominator = float(cost_vector.T @ precision_inverse @ cost_vector)
        self.value = (precision_inverse @ cost_vector) / denominator


class Loss:
    """Quadratic variance term at epsilon for the Lagrange multiplier search."""

    def __init__(self, coeff_a: float, coeff_b: float, coeff_c: float) -> None:
        self.coeff_a = coeff_a
        self.coeff_b = coeff_b
        self.coeff_c = coeff_c

    def __call__(self, epsilon: float) -> float:
        return self.coeff_a * epsilon * epsilon + self.coeff_b * epsilon + self.coeff_c


class Score:
    """CFVaR2 upper bound at epsilon."""

    def __init__(
        self,
        coeff_a: float,
        coeff_b: float,
        coeff_c: float,
        z_score: float,
    ) -> None:
        self.coeff_a = coeff_a
        self.coeff_b = coeff_b
        self.coeff_c = coeff_c
        self.z_score = z_score
        self.loss = Loss(coeff_a, coeff_b, coeff_c)

    def __call__(self, epsilon: float) -> float:
        term = self.loss(epsilon)
        if term <= 0.0:
            return float("inf")
        return -epsilon - self.z_score * math.sqrt(term)


class OptimalEpsilon:
    """Computes epsilon_star using Appendix B derivation.

    Preferred path: closed-form roots from Appendix B.
    Deterministic fallback: bounded numerical minimisation if root conditions fail.
    """

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        cost_vector: FloatArray,
        precision_matrix: FloatArray,
    ) -> None:
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.cost_vector = cost_vector
        self.precision_matrix = precision_matrix
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

        self.score = Score(coeff_a, coeff_b, coeff_c, z_score)
        candidate_solutions = []
        if abs(score_a) > 1e-12 and discriminant >= 0.0:
            epsilon_plus = (-score_b + math.sqrt(discriminant)) / (2.0 * score_a)
            epsilon_minus = (-score_b - math.sqrt(discriminant)) / (2.0 * score_a)
            if 2.0 * coeff_a * epsilon_plus + coeff_b > 0.0 and self.score(epsilon_plus) > 0.0:
                candidate_solutions.append(epsilon_plus)
            if 2.0 * coeff_a * epsilon_minus + coeff_b > 0.0 and self.score(epsilon_minus) > 0.0:
                candidate_solutions.append(epsilon_minus)

        if candidate_solutions:
            self.value = min(candidate_solutions, key=self.score)
            return

        search_radius = 1e3
        result = minimize_scalar(
            self.score, method="bounded", bounds=(-search_radius, search_radius)
        )
        if not result.success or not np.isfinite(result.fun):
            raise ValueError("Could not compute epsilon_star via closed-form or fallback solver")
        self.value = float(result.x)


class CFVaR2Closed:
    """Eq. (5)-(6) for P2 with determined epsilon_star. Returns optimal weights."""

    def __init__(
        self,
        precision_matrix: FloatArray,
        expected_payoff: FloatArray,
        cost_vector: FloatArray,
        alpha: float,
    ) -> None:
        self.precision_matrix = precision_matrix
        self.expected_payoff = expected_payoff
        self.cost_vector = cost_vector
        self.alpha = alpha
        epsilon_star = OptimalEpsilon(
            alpha=alpha,
            expected_payoff=expected_payoff,
            cost_vector=cost_vector,
            precision_matrix=precision_matrix,
        ).value
        precision_inverse = np.linalg.inv(precision_matrix)
        constraint_matrix = np.vstack([expected_payoff.T, cost_vector.T])
        dual_variable = np.array([epsilon_star, 1.0], dtype=float)
        left_factor = precision_inverse @ constraint_matrix.T
        right_factor = (
            np.linalg.inv(constraint_matrix @ precision_inverse @ constraint_matrix.T)
            @ dual_variable
        )
        self.value = left_factor @ right_factor


class CFVaR3Numerical:
    """Numerical solution for P3 with equality constraint x^T v = 1."""

    def __init__(
        self,
        cost_vector: FloatArray,
        initial_weights: FloatArray,
        objective_callable,
    ) -> None:
        self.cost_vector = cost_vector
        self.initial_weights = initial_weights
        self.objective_callable = objective_callable
        constraints = [{"type": "eq", "fun": lambda x: float(np.dot(x, cost_vector) - 1.0)}]
        result = minimize(
            objective_callable, x0=initial_weights, method="SLSQP", constraints=constraints
        )
        if not result.success:
            raise RuntimeError(f"Optimisation failed: {result.message}")
        self.value = np.asarray(result.x, dtype=float)


class CFVaR3Objective:
    """Callable wrapper around ``CFVaR3rd`` for use with scipy solvers."""

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        precision_matrix: FloatArray,
        kappa3_callback,
    ) -> None:
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.precision_matrix = precision_matrix
        self.kappa3_callback = kappa3_callback

    def __call__(self, weights: FloatArray) -> float:
        return CFVaR3rd(
            self.alpha,
            self.expected_payoff,
            self.precision_matrix,
            np.asarray(weights, dtype=float),
            float(self.kappa3_callback(weights)),
        ).value


class Risk:
    """Risk measure facade, removed in favour of direct class composition."""

    def __init__(self, alpha, expected_payoff, precision_matrix):
        self.alpha = alpha
        self.expected_payoff = expected_payoff
        self.precision_matrix = precision_matrix

    def second(self, weights: FloatArray) -> float:
        return CFVaR2nd(
            self.alpha,
            self.expected_payoff,
            self.precision_matrix,
            weights,
        ).value

    def third(self, weights: FloatArray, kappa3_callback) -> float:
        return CFVaR3rd(
            self.alpha,
            self.expected_payoff,
            self.precision_matrix,
            weights,
            float(kappa3_callback(weights)),
        ).value


class QualityScore:
    """Returns CFVaR2 value at closed-form solution for sanity checks."""

    def __init__(
        self,
        alpha: float,
        expected_payoff: FloatArray,
        cost_vector: FloatArray,
        precision_matrix: FloatArray,
    ) -> None:
        closed_form_weights = CFVaR2Closed(
            precision_matrix=precision_matrix,
            expected_payoff=expected_payoff,
            cost_vector=cost_vector,
            alpha=alpha,
        ).value
        self.value = CFVaR2nd(
            alpha=alpha,
            expected_payoff=expected_payoff,
            precision_matrix=precision_matrix,
            weights=closed_form_weights,
        ).value


class Greeks:
    """Theta, delta, gamma for a portfolio of options."""

    def __init__(
        self,
        weights: FloatArray,
        price_drift: FloatArray,
        delta_matrix: FloatArray,
        third_derivative: FloatArray,
    ) -> None:
        self.weights = weights
        self.price_drift = price_drift
        self.delta_matrix = delta_matrix
        self.third_derivative = third_derivative
        self.theta = float(price_drift.T @ weights)
        self.delta = delta_matrix @ weights
        self.gamma = np.einsum("m,mij->ij", weights, third_derivative)


class PortfolioVariance:
    """Direct scalar variance formula from Section 2.4."""

    def __init__(
        self,
        gamma_matrix: FloatArray,
        delta_vector: FloatArray,
        expected_payoff: FloatArray,
        covariance: FloatArray,
        degrees_of_freedom: float,
        c_coefficient: float,
        h: FloatArray,
    ) -> None:
        self.gamma_matrix = gamma_matrix
        self.delta_vector = delta_vector
        self.expected_payoff = expected_payoff
        self.covariance = covariance
        self.degrees_of_freedom = degrees_of_freedom
        self.c_coefficient = c_coefficient
        self.h = h
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
        self.value = float(term1 + term2 + term3 + term4 + term5 + term6 + term7)


class Linearize:
    """Build linearised expected return and precision matrix for the section-2.4 problem."""

    def __init__(
        self,
        price_drift: FloatArray,
        delta_matrix: FloatArray,
        third_derivative: FloatArray,
        expected_payoff: FloatArray,
        covariance: FloatArray,
        degrees_of_freedom: float,
        skewness: FloatArray,
        time_increment: float,
    ) -> None:
        instrument_count = third_derivative.shape[0]
        c_coefficient = Compute(degrees_of_freedom).value
        h = Linear(covariance, skewness).value

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

        q = Curvature(third_derivative=third_derivative, h=h).values
        hmatrix = Bilinear(
            delta_matrix=delta_matrix,
            budget_matrix=budget_matrix,
            covariance=covariance,
            third_derivative=third_derivative,
            h=h,
        ).matrix
        e = Cross(
            delta_matrix=delta_matrix,
            budget_matrix=budget_matrix,
            covariance=covariance,
            third_derivative=third_derivative,
            h=h,
        ).matrix

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

        self.dual_residual = dual_residual
        self.precision_matrix = 0.5 * (q_symmetric_part + q_symmetric_part.T)


class Reconstruct:
    """Reconstruct Q from portfolio variance evaluations."""

    def __init__(
        self,
        price_drift: FloatArray,
        delta_matrix: FloatArray,
        third_derivative: FloatArray,
        expected_payoff: FloatArray,
        covariance: FloatArray,
        degrees_of_freedom: float,
        skewness: FloatArray,
    ) -> None:
        instrument_count = third_derivative.shape[0]
        c_coefficient = Compute(degrees_of_freedom).value
        h = Linear(covariance, skewness).value

        def variance_at(xvec: FloatArray) -> float:
            greeks = Greeks(
                weights=xvec,
                price_drift=price_drift,
                delta_matrix=delta_matrix,
                third_derivative=third_derivative,
            )
            return PortfolioVariance(
                gamma_matrix=greeks.gamma,
                delta_vector=greeks.delta,
                expected_payoff=expected_payoff,
                covariance=covariance,
                degrees_of_freedom=degrees_of_freedom,
                c_coefficient=c_coefficient,
                h=h,
            ).value

        precision_matrix = np.zeros((instrument_count, instrument_count), dtype=float)
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
        self.value = precision_matrix
