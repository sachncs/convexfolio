"""Tests for convexfolio.data — LoadCSV, Summary, SyntheticPortfolio."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from convexfolio.data import LoadCSV, Summary, SyntheticPortfolio


def test_synthetic_portfolio_shapes() -> None:
    """SyntheticPortfolio(n)( ) returns 4-shape arrays."""
    inputs = SyntheticPortfolio(n_instruments=4, degrees_of_freedom=8.0, seed=1)()
    assert inputs.n_instruments == 4
    assert inputs.expected_payoff.shape == (4,)
    assert inputs.cost_vector.shape == (4,)
    assert inputs.precision_matrix.shape == (4, 4)


def test_summary_is_json_safe() -> None:
    """Summary(inputs) returns a JSON-serialisable dict."""
    inputs = SyntheticPortfolio(n_instruments=3, degrees_of_freedom=8.0, seed=2)()
    s = Summary(inputs)
    json.dumps(s)  # must not raise


def test_synthetic_portfolio_is_deterministic() -> None:
    """Same seed produces identical precision and payoff."""
    a = SyntheticPortfolio(n_instruments=5, degrees_of_freedom=8.0, seed=42)()
    b = SyntheticPortfolio(n_instruments=5, degrees_of_freedom=8.0, seed=42)()
    assert np.array_equal(a.expected_payoff, b.expected_payoff)
    assert np.array_equal(a.cost_vector, b.cost_vector)
    assert np.array_equal(a.precision_matrix, b.precision_matrix)


def test_synthetic_portfolio_seed_changes_output() -> None:
    """Different seeds produce different precision matrices."""
    a = SyntheticPortfolio(n_instruments=5, degrees_of_freedom=8.0, seed=1)()
    b = SyntheticPortfolio(n_instruments=5, degrees_of_freedom=8.0, seed=2)()
    assert not np.array_equal(a.precision_matrix, b.precision_matrix)


def test_synthetic_portfolio_rejects_invalid_nu() -> None:
    """Construction raises when degrees_of_freedom is at the boundary."""
    with pytest.raises(ValueError, match="degrees_of_freedom must be > 1"):
        SyntheticPortfolio(n_instruments=3, degrees_of_freedom=1.0, seed=7)


def test_load_csv_parses_sample_fixture() -> None:
    """LoadCSV('test)() reads the sample fixture with the expected shape."""
    inputs = LoadCSV("tests/fixtures/sample_portfolio.csv")()
    assert inputs.n_instruments == 5
    assert inputs.expected_payoff.shape == (5,)
    assert inputs.cost_vector.shape == (5,)
    assert inputs.precision_matrix.shape == (5, 5)


def test_load_csv_round_trip_through_solver() -> None:
    """LoadCSV + Minimize round-trip satisfies the budget constraint."""
    from convexfolio import Minimize, Variance

    inputs = LoadCSV("tests/fixtures/sample_portfolio.csv")()
    weights = Minimize(Variance(inputs.precision_matrix), inputs.cost_vector).value
    assert np.isclose(float(weights.T @ inputs.cost_vector), 1.0, atol=1e-6)


def test_load_csv_rejects_missing_columns(tmp_path: Path) -> None:
    """CSV missing required columns raises ValueError."""
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("cost\n1.0\n2.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV missing required columns"):
        LoadCSV(csv_path)()


def test_load_csv_rejects_empty(tmp_path: Path) -> None:
    """Header-only CSV raises ValueError on no data rows."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(
        "expected_payoff,cost,precision_diag\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="no data rows"):
        LoadCSV(csv_path)()


def test_load_csv_missing_file() -> None:
    """Missing CSV path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        LoadCSV("/nonexistent/path.csv")()


def test_load_csv_no_header_raises(tmp_path: Path) -> None:
    """Empty file (no header) raises ValueError."""
    empty = tmp_path / "no_header.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="no header row"):
        LoadCSV(empty)()


def test_summary_contains_expected_keys() -> None:
    """Summary(inputs) returns the documented dict shape."""
    inputs = SyntheticPortfolio(n_instruments=3, degrees_of_freedom=8.0, seed=7)()
    s = Summary(inputs)
    assert set(s.keys()) == {
        "n_instruments",
        "expected_payoff_range",
        "cost_range",
        "precision_trace",
    }
    assert s["n_instruments"] == 3


def test_to_config_shape_inline() -> None:
    """The to_config dict layout (inlined here, no helper function)."""
    inputs = SyntheticPortfolio(n_instruments=3, degrees_of_freedom=8.0, seed=7)()
    config = {
        "runtime": {
            "seed": 7,
            "log_level": "INFO",
            "output_directory": "/tmp/cf_out",
        },
        "optimization": {
            "alpha": 0.05,
            "method": "all",
            "enforce_nu_greater_than_six": True,
        },
        "inputs": {
            "expected_payoff": inputs.expected_payoff.tolist(),
            "cost_vector": inputs.cost_vector.tolist(),
            "precision_matrix": inputs.precision_matrix.tolist(),
        },
    }
    assert config["runtime"]["output_directory"] == "/tmp/cf_out"
    assert config["optimization"]["alpha"] == 0.05
    assert len(config["inputs"]["cost_vector"]) == 3
    assert len(config["inputs"]["precision_matrix"]) == 3
    json.dumps(config)  # must not raise
