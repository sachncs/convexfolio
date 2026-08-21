"""Performance benchmarks for the options package.

Run with:

    pytest --benchmark-only benchmarks/   # uses pytest-benchmark if installed
    pytest benchmarks/                     # plain wall-clock timings

Both modes produce comparable per-test numbers.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np
import pytest

from convexfolio.config import Experiment
from convexfolio.math import CFVaR2Closed, Minimize, Variance
from convexfolio.utils import reproduce

try:
    import pytest_benchmark  # noqa: F401
except ImportError:
    pytest_benchmark = None  # type: ignore[assignment]


_ITERS = 50
_BENCHMARK_PLUGIN = "benchmark"


def _wall_clock_run(test_name: str, func: Callable[[], object]) -> None:
    """Run ``_ITERS`` times and print the average wall-clock latency."""
    start = time.perf_counter()
    for _ in range(_ITERS):
        func()
    elapsed = time.perf_counter() - start
    avg_us = elapsed / _ITERS * 1e6
    print(f"\n{test_name}: {avg_us:.2f} us (avg of {_ITERS} runs)")


def _has_plugin(pytestconfig: pytest.Config) -> bool:
    return pytest_benchmark is not None and pytestconfig.pluginmanager.hasplugin(
        _BENCHMARK_PLUGIN
    )


def _run(
    pytestconfig: pytest.Config, test_name: str, func: Callable[[], object]
) -> None:
    if _has_plugin(pytestconfig):
        benchmark = pytestconfig.pluginmanager.getplugin(_BENCHMARK_PLUGIN)
        benchmark.pedantic(func, iterations=_ITERS, rounds=3)
    else:
        _wall_clock_run(test_name, func)


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
    return reproduce(Experiment())


def test_minimize_variance(
    portfolio: dict[str, np.ndarray],
    pytestconfig: pytest.Config,
) -> None:
    """Closed-form variance minimizer at 5/20/50 instruments."""
    _run(pytestconfig, "minimize_variance", lambda: minimize_action(portfolio))


def test_cfvar2_closed_form(
    portfolio: dict[str, np.ndarray],
    pytestconfig: pytest.Config,
) -> None:
    """Closed-form CFVaR2 weight solver at 5/20/50 instruments."""
    _run(pytestconfig, "cfvar2_closed_form", lambda: cfvar2_action(portfolio))


def test_reproduce(pytestconfig: pytest.Config) -> None:
    """Full single-run pipeline (default 5-instrument portfolio)."""
    _run(pytestconfig, "reproduce", reproduce_action)
