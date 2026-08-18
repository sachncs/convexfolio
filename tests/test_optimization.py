import numpy as np

from oop.optimization import solve_cfvar2_closed_form
from oop.optimization import solve_cfvar3_numerical
from oop.optimization import solve_variance_minimization


def test_variance_solution_satisfies_budget_constraint() -> None:
    precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
    cost_vector = np.array([1.2, 0.8])
    weights = solve_variance_minimization(cost_vector, precision_matrix)
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-8)


def test_cfvar2_closed_form_satisfies_affine_constraint() -> None:
    precision_matrix = np.array([[2.5, 0.0], [0.0, 1.5]])
    expected_payoff = np.array([0.1, 0.3])
    cost_vector = np.array([1.0, 2.0])
    weights = solve_cfvar2_closed_form(
        q_matrix=precision_matrix,
        u=expected_payoff,
        v=cost_vector,
        alpha=0.05,
    )
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-8)


def test_cfvar3_numerical_enforces_budget_constraint() -> None:
    cost_vector = np.array([1.0, 2.0, 1.5])

    def objective(x: np.ndarray) -> float:
        return float(np.sum(x**2))

    initial_weights = np.ones(3) / 3.0
    weights = solve_cfvar3_numerical(
        v=cost_vector,
        initial_x=initial_weights,
        objective_callable=objective,
    )
    assert np.isclose(float(weights.T @ cost_vector), 1.0, atol=1e-6)
