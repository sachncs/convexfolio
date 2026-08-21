"""Tests for convexfolio.plot."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import numpy as np
import pytest

from convexfolio.data import SyntheticPortfolio


@pytest.fixture()
def tmp_dir() -> Generator[Path]:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture()
def portfolio() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    return inputs.precision_matrix, inputs.cost_vector, inputs.expected_payoff


def test_weights_plot_writes_valid_png(tmp_dir: Path, portfolio: tuple) -> None:
    from convexfolio.plot import weights

    _, cost_vector, _ = portfolio
    out = tmp_dir / "weights.png"
    path = weights(cost_vector, output_path=out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 0
    with out.open("rb") as handle:
        assert handle.read(8) == b"\x89PNG\r\n\x1a\n", "not a PNG"


def test_weights_plot_with_labels(tmp_dir: Path) -> None:
    from convexfolio.plot import weights

    w = np.array([0.4, -0.2, 0.1, 0.3])
    out = tmp_dir / "weights_labeled.png"
    weights(w, labels=["A", "B", "C", "D"], output_path=out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_efficient_frontier_plot(tmp_dir: Path, portfolio: tuple) -> None:
    from convexfolio.plot import efficient_frontier

    Q, v, u = portfolio
    out = tmp_dir / "frontier.png"
    path = efficient_frontier(Q, v, u, output_path=out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_efficient_frontier_with_custom_alphas(
    tmp_dir: Path, portfolio: tuple
) -> None:
    from convexfolio.plot import efficient_frontier

    Q, v, u = portfolio
    out = tmp_dir / "frontier_custom.png"
    efficient_frontier(Q, v, u, alphas=[0.01, 0.05, 0.10, 0.20], output_path=out)
    assert out.exists()


def test_cfvar_sensitivity_plot(tmp_dir: Path, portfolio: tuple) -> None:
    from convexfolio.plot import cfvar_sensitivity

    Q, v, u = portfolio
    out = tmp_dir / "cfvar.png"
    path = cfvar_sensitivity(Q, v, u, output_path=out)
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_plots_create_parent_directories(tmp_path: Path) -> None:
    from convexfolio.plot import weights

    nested = tmp_path / "deep" / "nested" / "dir"
    out = nested / "w.png"
    weights(np.array([0.5, 0.5]), output_path=out)
    assert out.exists()


def test_plot_module_lazy_loads_matplotlib() -> None:
    """Importing convexfolio.plot should not require matplotlib to be
    importable until a plot function is actually called."""
    import convexfolio.plot as plot_mod  # noqa: F401

    assert hasattr(plot_mod, "weights")
    assert hasattr(plot_mod, "efficient_frontier")
    assert hasattr(plot_mod, "cfvar_sensitivity")
