import numpy as np

from options.math import MinimizeVariance
from options.math import SolveCFVaR2ClosedForm
from options.math import SolveCFVaR3Numerical


def test_variance_solution_satisfies_budget_constraint() -> None:
    precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
    cost_vector = np.array([1.2, 0.8])
    weights = MinimizeVariance(cost_vector, precision_matrix).value
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-8)


def test_cfvar2_closed_form_satisfies_affine_constraint() -> None:
    precision_matrix = np.array([[2.5, 0.0], [0.0, 1.5]])
    expected_payoff = np.array([0.1, 0.3])
    cost_vector = np.array([1.0, 2.0])
    weights = SolveCFVaR2ClosedForm(
        precision_matrix=precision_matrix,
        expected_payoff=expected_payoff,
        cost_vector=cost_vector,
        alpha=0.05,
    ).value
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-8)


def test_cfvar3_numerical_enforces_budget_constraint() -> None:
    cost_vector = np.array([1.0, 2.0, 1.5])

    def objective(x: np.ndarray) -> float:
        return float(np.sum(x**2))

    initial_weights = np.ones(3) / 3.0
    weights = SolveCFVaR3Numerical(
        cost_vector=cost_vector,
        initial_weights=initial_weights,
        objective_callable=objective,
    ).value
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-6)
