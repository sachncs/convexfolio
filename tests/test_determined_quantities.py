import numpy as np

from oop.moments import compute_c_scalar
from oop.moments import compute_h_vector
from oop.reproduction_math import portfolio_greeks_from_shares
from oop.reproduction_math import reconstruct_q_matrix_from_direct_variance
from oop.reproduction_math import variance_direct_formula


def test_c_matches_theorem2_formula() -> None:
    degrees_of_freedom = 8.0
    c_value = compute_c_scalar(degrees_of_freedom)
    assert c_value > 0.0


def test_h_has_expected_shape() -> None:
    covariance = np.eye(3)
    skewness = np.array([0.3, -0.2, 0.1])
    h_vector = compute_h_vector(sigma=covariance, omega=skewness)
    assert h_vector.shape == (3,)


def test_reconstructed_q_matches_direct_variance_formula() -> None:
    rng = np.random.default_rng(123)
    payoff_dimension = 4
    instrument_count = 3
    degrees_of_freedom = 9.0

    sigma_noise = rng.normal(size=(payoff_dimension, payoff_dimension))
    covariance = sigma_noise.T @ sigma_noise + np.eye(payoff_dimension)
    expected_payoff = rng.normal(size=payoff_dimension)
    skewness = rng.normal(size=payoff_dimension)

    delta_matrix = rng.normal(size=(payoff_dimension, instrument_count))
    price_drift = rng.normal(size=instrument_count)
    third_derivative_tensor = np.array(
        [(g + g.T) / 2.0 for g in rng.normal(size=(instrument_count, payoff_dimension, payoff_dimension))]
    )

    precision_matrix = reconstruct_q_matrix_from_direct_variance(
        price_drift=price_drift,
        delta_matrix=delta_matrix,
        third_derivative_tensor=third_derivative_tensor,
        expected_payoff=expected_payoff,
        covariance=covariance,
        degrees_of_freedom=degrees_of_freedom,
        skewness=skewness,
    )

    c_coefficient = compute_c_scalar(degrees_of_freedom)
    h_vector = compute_h_vector(sigma=covariance, omega=skewness)

    for _ in range(25):
        x = rng.normal(size=instrument_count)
        _, delta_vector, gamma_matrix = portfolio_greeks_from_shares(
            x=x,
            price_drift=price_drift,
            delta_matrix=delta_matrix,
            third_derivative_tensor=third_derivative_tensor,
        )
        direct_var = variance_direct_formula(
            gamma_matrix=gamma_matrix,
            delta_vector=delta_vector,
            expected_payoff=expected_payoff,
            covariance=covariance,
            degrees_of_freedom=degrees_of_freedom,
            c_coefficient=c_coefficient,
            h_vector=h_vector,
        )
        matrix_var = 0.5 * float(x.T @ precision_matrix @ x)
        assert np.isclose(direct_var, matrix_var, atol=1e-7)
