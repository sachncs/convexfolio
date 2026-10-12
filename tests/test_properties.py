"""Deterministic property-style checks over generated valid portfolios."""

import numpy as np
import pytest

from convexfolio import Matrix, Vector
from convexfolio.config import PortfolioInputs
from convexfolio.constraints import budget_residual, leverage_cap_inequality
from convexfolio.math import Minimize, Variance


@pytest.mark.parametrize("seed", range(8))
def test_generated_valid_portfolios_preserve_value_and_budget_invariants(
    seed: int,
) -> None:
    """Every generated positive-definite portfolio satisfies core invariants."""
    rng = np.random.default_rng(seed)
    instrument_count = 2 + seed % 5
    sample = rng.normal(size=(instrument_count, instrument_count))
    precision_matrix = sample.T @ sample + 0.25 * np.eye(instrument_count)
    expected_payoff = rng.normal(size=instrument_count)
    cost_vector = rng.uniform(0.1, 2.0, size=instrument_count)
    inputs = PortfolioInputs(expected_payoff, cost_vector, precision_matrix)

    assert isinstance(inputs.expected_payoff, Vector)
    assert isinstance(inputs.cost_vector, Vector)
    assert isinstance(inputs.precision_matrix, Matrix)
    weights = Minimize(Variance(inputs.precision_matrix), inputs.cost_vector).value
    assert np.all(np.isfinite(weights))
    assert budget_residual(inputs.cost_vector, weights) == pytest.approx(0.0, abs=1e-8)
    leverage_constraint = leverage_cap_inequality(
        instrument_count, float(np.sum(np.abs(weights)) + 1.0)
    )
    assert float(leverage_constraint["fun"](weights)) >= 0.0


def test_generated_vectors_are_owned_and_read_only() -> None:
    source = np.array([1.0, 2.0, 3.0])
    vector = Vector(source)
    source[0] = 100.0
    assert vector[0] == pytest.approx(1.0)
    assert not vector.flags.writeable
    copied = vector.copy()
    copied[0] = 100.0
    assert vector[0] == pytest.approx(1.0)
