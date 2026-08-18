"""Performance benchmarks for the options package.

Uses ``pytest-benchmark`` to record timings. Run with:

    pytest --benchmark-only benchmarks/

or simply ``pytest benchmarks/`` to mix benchmarks with normal tests.
"""

from __future__ import annotations

import numpy as np
import pytest

from options.config import Experiment
from options.math import CFVaR2Closed
from options.math import CFVaR3Numerical
from options.math import CFVaR3Objective
from options.math import Minimize
from options.math import Variance
from options.utils import reproduce


@pytest.fixture(params=[5, 20, 50])
def portfolio(request: pytest.FixtureRequest) -> dict[str, np.ndarray]:
    """Generate a synthetic portfolio of ``n_instruments`` options."""
    n_instruments = request.param
    rng = np.random.default_rng(42)
    sample_matrix = rng.normal(size=(n_instruments, n_instruments))
    precision_matrix = sample_matrix.T @ sample_matrix + 0.5 * np.eye(n_instruments)
    cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
    expected_payoff_vector = rng.normal(size=n_instruments)
    return {
        "precision_matrix": precision_matrix,
        "cost_vector": cost_vector,
        "expected_payoff_vector": expected_payoff_vector,
    }


def test_minimize_variance(
    benchmark: pytest.BenchmarkFixture, portfolio: dict[str, np.ndarray]
) -> None:
    """Closed-form variance minimiser."""

    def run() -> np.ndarray:
        return Minimize(
            Variance(portfolio["precision_matrix"]), portfolio["cost_vector"]
        ).value

    benchmark(run)


def test_cfvar2_closed_form(
    benchmark: pytest.BenchmarkFixture, portfolio: dict[str, np.ndarray]
) -> None:
    """Closed-form CFVaR2 weight solver."""

    def run() -> np.ndarray:
        return CFVaR2Closed(
            precision_matrix=portfolio["precision_matrix"],
            expected_payoff=portfolio["expected_payoff_vector"],
            cost_vector=portfolio["cost_vector"],
            alpha=0.05,
        ).value

    benchmark(run)


def test_reproduce(benchmark: pytest.BenchmarkFixture) -> None:
    """Full single-run pipeline."""

    def run() -> dict[str, object]:
        return reproduce(Experiment())

    benchmark(run)


@pytest.mark.skip(reason="Inner-loop wrapper; covered indirectly by reproduce.")
def test_cfvar3_numerical(
    benchmark: pytest.BenchmarkFixture, portfolio: dict[str, np.ndarray]
) -> None:
    """Numerical CFVaR3 weight solver.

    The inner objective is a closure with many captured constants; keeping
    it small here would not capture the realistic workload, so we run the
    real CFVaR3Numerical path against a trivial objective.
    """

    objective = CFVaR3Objective(
        alpha=0.05,
        expected_payoff=portfolio["expected_payoff_vector"],
        precision_matrix=portfolio["precision_matrix"],
        kappa3_callback=lambda x: 0.0,
    )
    initial_weights = np.ones(portfolio["precision_matrix"].shape[0])
    initial_weights = initial_weights / initial_weights.sum()

    def run() -> np.ndarray:
        return CFVaR3Numerical(
            cost_vector=portfolio["cost_vector"],
            initial_weights=initial_weights,
            objective_callable=objective,
        ).value

    benchmark(run)
