"""Tests for convexfolio.backtest."""

from __future__ import annotations

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
from convexfolio.constraints import long_only_inequalities
from convexfolio.data import synthetic_portfolio


@pytest.fixture()
def tmp_dir() -> Generator[Path]:
    import tempfile

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
    prices = np.zeros((3, 4))
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


def test_load_price_history_csv_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_price_history_csv("/nonexistent/path.csv")


def test_run_backtest_short_history_raises() -> None:
    inputs = synthetic_portfolio(3, 8.0, 7)
    prices = np.ones((1, 3))
    h = PriceHistory(timestamps=np.array(["t0"]), prices=prices)
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=1)
    with pytest.raises(ValueError, match="at least 2 timestamps"):
        run_backtest(h, cfg)


def test_run_backtest_basic_shape(history: PriceHistory) -> None:
    inputs = synthetic_portfolio(5, 8.0, 7)
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
    inputs = synthetic_portfolio(5, 8.0, 7)
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
    inputs = synthetic_portfolio(5, 8.0, 7)
    cfg = BacktestConfig(
        portfolio_inputs=inputs,
        rebalance_frequency=history.n_timestamps + 1,
        transaction_cost_bps=0.0,
    )
    result = run_backtest(history, cfg)
    assert result.cumulative_costs[-1] == 0.0


def test_run_backtest_with_long_only_constraints(history: PriceHistory) -> None:
    """Long-only should keep all weights non-negative."""
    inputs = synthetic_portfolio(5, 8.0, 7)
    cfg = BacktestConfig(
        portfolio_inputs=inputs,
        rebalance_frequency=1,
        transaction_cost_bps=5.0,
        extra_constraints=tuple(long_only_inequalities(5)),
    )
    result = run_backtest(history, cfg)
    assert np.all(result.weights >= -1e-8), f"weights {result.weights}"


def test_run_backtest_rejects_zero_rebalance_frequency(history: PriceHistory) -> None:
    inputs = synthetic_portfolio(5, 8.0, 7)
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=0)
    with pytest.raises(ValueError, match="rebalance_frequency must be >= 1"):
        run_backtest(history, cfg)


def test_run_backtest_json_safe_summary(history: PriceHistory) -> None:
    import json

    inputs = synthetic_portfolio(5, 8.0, 7)
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=2)
    result = run_backtest(history, cfg)
    json.dumps(result.summary)  # must not raise


def test_run_backtest_first_value_is_one(history: PriceHistory) -> None:
    """Initial portfolio value is always 1.0 (normalised)."""
    inputs = synthetic_portfolio(5, 8.0, 7)
    cfg = BacktestConfig(portfolio_inputs=inputs, rebalance_frequency=1)
    result = run_backtest(history, cfg)
    assert result.portfolio_value[0] == pytest.approx(1.0, abs=1e-9)
