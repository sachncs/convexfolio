"""Tests for convexfolio.backtest."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from pathlib import Path

import numpy as np
import pytest

from convexfolio.backtest import (
    BacktestConfig,
    BacktestResult,
    PriceHistory,
    load_price_history_csv,
    run_backtest,
)
from convexfolio.config import PortfolioInputs
from convexfolio.constraints import long_only_inequalities
from convexfolio.data import SyntheticPortfolio
from convexfolio.errors import ValidationError


@pytest.fixture()
def tmp_dir() -> Generator[Path]:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture()
def history() -> PriceHistory:
    prices = np.array(
        [
            [1.00, 1.00, 1.00, 1.00, 1.00],
            [1.05, 0.98, 1.02, 0.95, 1.03],
            [1.08, 0.96, 1.05, 0.92, 1.06],
            [1.04, 1.02, 1.08, 0.98, 1.10],
            [1.10, 0.99, 1.12, 0.95, 1.07],
        ]
    )
    return PriceHistory(
        timestamps=np.array(["t0", "t1", "t2", "t3", "t4"]),
        prices=prices,
    )


def test_price_history_properties() -> None:
    prices = np.ones((3, 4))
    h = PriceHistory(timestamps=np.array(["a", "b", "c"]), prices=prices)
    assert h.n_timestamps == 3
    assert h.n_instruments == 4


def test_load_price_history_csv_round_trip(tmp_dir: Path) -> None:
    csv_path = tmp_dir / "prices.csv"
    csv_path.write_text(
        "timestamp,A,B\n2026-01-01,1.0,2.0\n2026-01-02,1.1,2.1\n",
        encoding="utf-8",
    )
    history = load_price_history_csv(csv_path)
    assert history.n_timestamps == 2
    assert history.n_instruments == 2
    assert history.timestamps[0] == "2026-01-01"
    assert float(history.prices[0, 0]) == 1.0


def test_load_price_history_csv_rejects_missing_timestamp(tmp_dir: Path) -> None:
    csv_path = tmp_dir / "bad.csv"
    csv_path.write_text("date,A\n1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be 'timestamp'"):
        load_price_history_csv(csv_path)


def test_load_price_history_csv_rejects_empty(tmp_dir: Path) -> None:
    csv_path = tmp_dir / "empty.csv"
    csv_path.write_text("timestamp,A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no data rows"):
        load_price_history_csv(csv_path)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("timestamp,A,A\n1,1,2\n2,1,2\n", "unique"),
        ("timestamp,A\n1\n2,1,2\n", "match"),
        ("timestamp,A\n,1\n", "timestamp"),
    ],
)
def test_load_price_history_csv_rejects_malformed_rows(
    tmp_dir: Path, content: str, message: str
) -> None:
    csv_path = tmp_dir / "malformed.csv"
    csv_path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_price_history_csv(csv_path)


def test_load_price_history_csv_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_price_history_csv("/nonexistent/path.csv")


def test_run_backtest_short_history_raises() -> None:
    inputs = SyntheticPortfolio(3, 8.0, 7)()
    prices = np.ones((1, 3))
    h = PriceHistory(timestamps=np.array(["t0"]), prices=prices)
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=1)
    with pytest.raises(ValueError, match="at least 2 timestamps"):
        run_backtest(h, cfg)


def test_run_backtest_basic_shape(history: PriceHistory) -> None:
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(
        portfolio_inputs=inputs, rebalance_frequency=2, transaction_cost_bps=5.0
    )
    result = run_backtest(history, cfg)
    assert isinstance(result, BacktestResult)
    assert result.weights.shape == (history.n_timestamps, history.n_instruments)
    assert result.portfolio_value.shape == (history.n_timestamps,)
    assert result.turnover.shape == (history.n_timestamps,)
    assert result.cumulative_costs.shape == (history.n_timestamps,)
    assert len(result.timestamps) == history.n_timestamps


def test_run_backtest_summary_keys(history: PriceHistory) -> None:
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=2)
    result = run_backtest(history, cfg)
    expected_keys = {
        "n_timestamps",
        "n_instruments",
        "rebalance_frequency",
        "transaction_cost_bps",
        "alpha",
        "final_portfolio_value",
        "total_turnover",
        "total_costs",
        "max_drawdown",
    }
    assert set(result.summary.keys()) == expected_keys


def test_run_backtest_zero_costs_when_rebalance_frequency_exceeds_history(
    history: PriceHistory,
) -> None:
    """If rebalance_frequency > n_timestamps, only the initial rebalance fires."""
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(
        portfolio_inputs=inputs,
        rebalance_frequency=history.n_timestamps + 1,
        transaction_cost_bps=0.0,
    )
    result = run_backtest(history, cfg)
    assert result.cumulative_costs[-1] == 0.0


def test_run_backtest_with_long_only_constraints(history: PriceHistory) -> None:
    """Long-only should keep all weights non-negative."""
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(
        portfolio_inputs=inputs,
        rebalance_frequency=1,
        transaction_cost_bps=5.0,
        extra_constraints=tuple(long_only_inequalities(5)),
    )
    result = run_backtest(history, cfg)
    assert np.all(result.weights >= -1e-8), f"weights {result.weights}"


def test_run_backtest_rejects_zero_rebalance_frequency(history: PriceHistory) -> None:
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    with pytest.raises(ValueError, match="rebalance_frequency must be >= 1"):
        BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=0)


def test_backtest_config_rejects_invalid_cost_and_alpha() -> None:
    inputs = SyntheticPortfolio(3, 8.0, 7)()
    with pytest.raises(ValidationError, match="transaction_cost_bps"):
        BacktestConfig(portfolio_inputs=inputs, transaction_cost_bps=-1.0)
    with pytest.raises(ValidationError, match="alpha"):
        BacktestConfig(portfolio_inputs=inputs, alpha=0.5)


def test_run_backtest_json_safe_summary(history: PriceHistory) -> None:
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=2)
    result = run_backtest(history, cfg)
    json.dumps(result.summary)  # must not raise


def test_run_backtest_first_value_is_one(history: PriceHistory) -> None:
    """Initial portfolio value is always 1.0 (normalised)."""
    inputs = SyntheticPortfolio(5, 8.0, 7)()
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=1)
    result = run_backtest(history, cfg)
    assert result.portfolio_value[0] == pytest.approx(1.0, abs=1e-9)


def test_run_backtest_marks_portfolio_to_market() -> None:
    """Held positions change portfolio value when prices move."""
    inputs = PortfolioInputs(
        expected_payoff=np.array([0.1, 0.1]),
        cost_vector=np.array([1.0, 1.0]),
        precision_matrix=np.eye(2),
    )
    history = PriceHistory(
        timestamps=np.array(["t0", "t1"]),
        prices=np.array([[1.0, 1.0], [2.0, 2.0]]),
    )
    result = run_backtest(
        history,
        BacktestConfig(portfolio_inputs=inputs, transaction_cost_bps=0.0),
    )
    assert result.portfolio_value[-1] == pytest.approx(2.0)


def test_price_history_rejects_non_positive_prices() -> None:
    """Price histories cannot contain zero or negative prices."""
    with pytest.raises(ValidationError, match="positive"):
        PriceHistory(
            timestamps=np.array(["t0"]),
            prices=np.array([[0.0]]),
        )


def test_price_history_rejects_mismatched_rows() -> None:
    with pytest.raises(ValidationError, match="one row per timestamp"):
        PriceHistory(
            timestamps=np.array(["t0", "t1"]),
            prices=np.array([[1.0]]),
        )


def test_tolerated_solver_failure_uses_budget_feasible_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = PortfolioInputs(
        expected_payoff=np.array([0.1, 0.1]),
        cost_vector=np.array([1.0, 1.0]),
        precision_matrix=np.eye(2),
    )
    history = PriceHistory(
        timestamps=np.array(["t0", "t1"]),
        prices=np.array([[1.0, 1.0], [2.0, 2.0]]),
    )

    def fail_solver(*args, **kwargs):
        raise RuntimeError("synthetic solver failure")

    monkeypatch.setattr("convexfolio.backtest.CFVaR3Numerical", fail_solver)
    result = run_backtest(
        history,
        BacktestConfig(
            portfolio_inputs=inputs,
            tolerate_solver_failure=True,
            transaction_cost_bps=0.0,
        ),
    )
    assert result.portfolio_value[-1] == pytest.approx(2.0)
    assert np.allclose(result.weights[0] * history.prices[0], 0.5)


def test_tolerated_solver_failure_rejects_invalid_extra_constraint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = SyntheticPortfolio(2, 8.0, 7)()
    history = PriceHistory(
        timestamps=np.array(["t0", "t1"]),
        prices=np.ones((2, 2)),
    )

    def fail_solver(*args, **kwargs):
        raise RuntimeError("synthetic solver failure")

    monkeypatch.setattr("convexfolio.backtest.CFVaR3Numerical", fail_solver)
    with pytest.raises(RuntimeError, match="violated"):
        run_backtest(
            history,
            BacktestConfig(
                portfolio_inputs=inputs,
                tolerate_solver_failure=True,
                extra_constraints=(
                    {"type": "ineq", "fun": lambda weights: -1.0},
                ),
            ),
        )
