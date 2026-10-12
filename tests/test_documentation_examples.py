"""Executable examples copied from the user-facing documentation."""

import numpy as np

from convexfolio import Matrix, Minimize, Variance, Vector


def test_getting_started_core_example() -> None:
    """The introductory two-instrument example remains executable."""
    precision_matrix = Matrix([[2.0, 0.1], [0.1, 1.5]]).validate()
    cost_vector = Vector([0.60, 0.40]).validate(positive=True)

    weights = Minimize(Variance(precision_matrix), cost_vector).value

    assert np.allclose(weights, [1.0591133, 0.91133005], atol=1e-7)
    np.testing.assert_allclose(float(weights @ cost_vector), 1.0, atol=1e-8)
