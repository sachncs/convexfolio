"""Tests for convexfolio.data."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from convexfolio.data import load_csv, synthetic_portfolio, to_config


def test_portfolio_inputs_n_instruments() -> None:
    inputs = synthetic_portfolio(n_instruments=4, degrees_of_freedom=8.0, seed=1)
    assert inputs.n_instruments == 4
    assert inputs.expected_payoff.shape == (4,)
    assert inputs.cost_vector.shape == (4,)
    assert inputs.precision_matrix.shape == (4, 4)


def test_portfolio_inputs_summary_is_json_safe() -> None:
    import json

    from convexfolio.data import summary

    inputs = synthetic_portfolio(n_instruments=3, degrees_of_freedom=8.0, seed=2)
    s = summary(inputs)
    json.dumps(s)  # must not raise


def test_synthetic_portfolio_is_deterministic() -> None:
    a = synthetic_portfolio(n_instruments=5, degrees_of_freedom=8.0, seed=42)
    b = synthetic_portfolio(n_instruments=5, degrees_of_freedom=8.0, seed=42)
    assert np.array_equal(a.expected_payoff, b.expected_payoff)
    assert np.array_equal(a.cost_vector, b.cost_vector)
    assert np.array_equal(a.precision_matrix, b.precision_matrix)


def test_synthetic_portfolio_seed_changes_output() -> None:
    a = synthetic_portfolio(n_instruments=5, degrees_of_freedom=8.0, seed=1)
    b = synthetic_portfolio(n_instruments=5, degrees_of_freedom=8.0, seed=2)
    assert not np.array_equal(a.precision_matrix, b.precision_matrix)


def test_synthetic_portfolio_rejects_invalid_nu() -> None:
    import pytest

    with pytest.raises(ValueError, match="degrees_of_freedom must be > 1"):
        synthetic_portfolio(n_instruments=3, degrees_of_freedom=1.0, seed=7)


def test_load_csv_parses_sample_fixture() -> None:
    inputs = load_csv("tests/fixtures/sample_portfolio.csv")
    assert inputs.n_instruments == 5
    assert inputs.expected_payoff.shape == (5,)
    assert inputs.cost_vector.shape == (5,)
    assert inputs.precision_matrix.shape == (5, 5)


def test_load_csv_round_trip_through_solver() -> None:
    from convexfolio import Minimize, Variance

    inputs = load_csv("tests/fixtures/sample_portfolio.csv")
    weights = Minimize(Variance(inputs.precision_matrix), inputs.cost_vector).value
    assert np.isclose(float(weights.T @ inputs.cost_vector), 1.0, atol=1e-6)


def test_load_csv_rejects_missing_columns(tmp_path: Path) -> None:
    import pytest

    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("cost\n1.0\n2.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV missing required columns"):
        load_csv(csv_path)


def test_load_csv_rejects_empty(tmp_path: Path) -> None:
    import pytest

    csv_path = tmp_path / "empty.csv"
    csv_path.write_text(
        "expected_payoff,cost,precision_diag\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="no data rows"):
        load_csv(csv_path)


def test_load_csv_missing_file() -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        load_csv("/nonexistent/path.csv")


def test_to_config_shape() -> None:
    inputs = synthetic_portfolio(n_instruments=3, degrees_of_freedom=8.0, seed=7)
    config = to_config(inputs, output_directory="/tmp/cf_out")
    assert config["runtime"]["output_directory"] == "/tmp/cf_out"
    assert config["optimization"]["alpha"] == 0.05
    assert len(config["inputs"]["cost_vector"]) == 3
    assert len(config["inputs"]["precision_matrix"]) == 3
    import json

    json.dumps(config)  # must not raise
