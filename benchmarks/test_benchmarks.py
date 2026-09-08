"""Performance benchmarks for the options package.

Run with:

    pytest --benchmark-only benchmarks/   # uses pytest-benchmark

This module requires ``pytest-benchmark`` (declared as a runtime
dependency in ``pyproject.toml``).
"""

from __future__ import annotations

import numpy as np
import pytest
import pytest_benchmark

from convexfolio.config import Experiment
from convexfolio.math import CFVaR2Closed, Minimize, Variance
from convexfolio.utils import Reproduce

ITERATIONS_PER_RUN = 50
ROUNDS = 3


@pytest.fixture(params=[5, 20, 50])
def portfolio(request: pytest.FixtureRequest) -> dict[str, np.ndarray]:
    """Synthetic portfolio of ``n_instruments`` options."""
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


def minimize_action(portfolio: dict[str, np.ndarray]) -> np.ndarray:
    """Action under benchmark: closed-form variance minimizer."""
    return Minimize(
        Variance(portfolio["precision_matrix"]), portfolio["cost_vector"]
    ).value


def cfvar2_action(portfolio: dict[str, np.ndarray]) -> np.ndarray:
    """Action under benchmark: closed-form CFVaR2 weight solver."""
    return CFVaR2Closed(
        precision_matrix=portfolio["precision_matrix"],
        expected_payoff=portfolio["expected_payoff_vector"],
        cost_vector=portfolio["cost_vector"],
        alpha=0.05,
    ).value


def reproduce_action() -> dict[str, object]:
    """Action under benchmark: full single-run pipeline."""
    return Reproduce(Experiment())()


def test_minimize_variance(
    benchmark: pytest_benchmark.BenchmarkFixture,
    portfolio: dict[str, np.ndarray],
) -> None:
    """Closed-form variance minimizer at 5/20/50 instruments."""
    benchmark.pedantic(
        lambda: minimize_action(portfolio),
        iterations=ITERATIONS_PER_RUN,
        rounds=ROUNDS,
    )


def test_cfvar2_closed_form(
    benchmark: pytest_benchmark.BenchmarkFixture,
    portfolio: dict[str, np.ndarray],
) -> None:
    """Closed-form CFVaR2 weight solver at 5/20/50 instruments."""
    benchmark.pedantic(
        lambda: cfvar2_action(portfolio),
        iterations=ITERATIONS_PER_RUN,
        rounds=ROUNDS,
    )


def test_reproduce(benchmark: pytest_benchmark.BenchmarkFixture) -> None:
    """Full single-run pipeline (default 5-instrument portfolio)."""
    benchmark.pedantic(
        reproduce_action, iterations=ITERATIONS_PER_RUN, rounds=ROUNDS
    )
