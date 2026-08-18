import numpy as np

from options.math import Compute, Greeks, Linear, PortfolioVariance, Reconstruct


def test_c_matches_theorem2_formula() -> None:
    degrees_of_freedom = 8.0
    c_value = Compute(degrees_of_freedom).value
    assert c_value > 0.0


def test_h_has_expected_shape() -> None:
    covariance = np.eye(3)
    skewness = np.array([0.3, -0.2, 0.1])
    h_vector = Linear(covariance, skewness).value
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
    third_derivative = np.array(
        [
            (g + g.T) / 2.0
            for g in rng.normal(
                size=(instrument_count, payoff_dimension, payoff_dimension)
            )
        ]
    )

    precision_matrix = Reconstruct(
        price_drift=price_drift,
        delta_matrix=delta_matrix,
        third_derivative=third_derivative,
        expected_payoff=expected_payoff,
        covariance=covariance,
        degrees_of_freedom=degrees_of_freedom,
        skewness=skewness,
    ).value

    c_coefficient = Compute(degrees_of_freedom).value
    h_vector = Linear(covariance, skewness).value

    for _ in range(25):
        x = rng.normal(size=instrument_count)
        greeks = Greeks(
            weights=x,
            price_drift=price_drift,
            delta_matrix=delta_matrix,
            third_derivative=third_derivative,
        )
        direct_var = PortfolioVariance(
            gamma_matrix=greeks.gamma,
            delta_vector=greeks.delta,
            expected_payoff=expected_payoff,
            covariance=covariance,
            degrees_of_freedom=degrees_of_freedom,
            c_coefficient=c_coefficient,
            h=h_vector,
        ).value
        matrix_var = 0.5 * float(x.T @ precision_matrix @ x)
        assert np.isclose(direct_var, matrix_var, atol=1e-7)
