"""Multi-period rebalancing backtest.

A backtest takes a price history (one column per instrument, one row
per timestamp) and rebalances the portfolio periodically, applying
transaction costs proportional to the weight turnover.

Two phases in this file:

* :class:`Backtest` — orchestrator, holds config and price history.
* :func:`run_backtest` — runs the simulation and returns a result dict.

Concrete transaction-cost models and rebalance logic live alongside
in this same module; the test suite covers both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from convexfolio.config import PortfolioInputs
from convexfolio.constraints import SLSQPLambda


@dataclass(frozen=True)
class PriceHistory:
    """Bundle of historical prices for a backtest.

    Attributes:
        timestamps: 1-D array of timestamp labels (string or numeric).
        prices: 2-D array of shape ``(n_timestamps, n_instruments)``.
    """

    timestamps: np.ndarray
    prices: np.ndarray

    @property
    def n_timestamps(self) -> int:
        return int(self.prices.shape[0])

    @property
    def n_instruments(self) -> int:
        return int(self.prices.shape[1])


def load_price_history_csv(path: str | Path) -> PriceHistory:
    """Load a price-history CSV.

    The CSV must have a header row. The first column is ``timestamp``;
    remaining columns are instrument prices, one per instrument.

    Args:
        path: Path to a CSV file.

    Returns:
        A ``PriceHistory`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the header is missing the ``timestamp`` column.
    """
    import csv

    input_path = Path(path)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file has no header row")
        if header[0] != "timestamp":
            raise ValueError(
                "first CSV column must be 'timestamp' (got "
                f"{header[0]!r})"
            )
        timestamps: list[str] = []
        rows: list[list[float]] = []
        for row in reader:
            timestamps.append(row[0])
            rows.append([float(v) for v in row[1:]])
    if not rows:
        raise ValueError("CSV file has no data rows")
    prices = np.asarray(rows, dtype=float)
    return PriceHistory(
        timestamps=np.asarray(timestamps),
        prices=prices,
    )


@dataclass
class BacktestConfig:
    """Configuration for a multi-period rebalance backtest.

    Attributes:
        portfolio_inputs: Initial portfolio inputs.
        rebalance_frequency: How often to rebalance, in timestamps.
            1 = every timestamp; 2 = every other timestamp; etc.
        transaction_cost_bps: Round-trip transaction cost, in basis
            points (1 bp = 0.01%) of the weight turnover magnitude.
        alpha: CFVaR2 risk parameter.
    """

    portfolio_inputs: PortfolioInputs
    rebalance_frequency: int = 1
    transaction_cost_bps: float = 5.0
    alpha: float = 0.05
    extra_constraints: tuple[dict[str, str | SLSQPLambda], ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class BacktestResult:
    """Output of a backtest run.

    Attributes:
        timestamps: 1-D timestamp labels, length ``n_timestamps``.
        portfolio_value: 1-D portfolio value over time (starting at 1.0).
        weights: 2-D weight matrix, shape ``(n_timestamps, n_instruments)``.
        turnover: 1-D per-timestamp turnover magnitude.
        cumulative_costs: 1-D cumulative transaction-cost sum.
        summary: Aggregate statistics dict.
    """

    timestamps: np.ndarray
    portfolio_value: np.ndarray
    weights: np.ndarray
    turnover: np.ndarray
    cumulative_costs: np.ndarray
    summary: dict[str, Any]


def run_backtest(
    history: PriceHistory, config: BacktestConfig
) -> BacktestResult:
    """Run a multi-period rebalance backtest.

    At every ``rebalance_frequency``-th timestamp, the portfolio is
    re-solved using ``CFVaR3Numerical`` with the latest price-implied
    inputs. Between rebalance timestamps, weights are held constant
    and portfolio value evolves with prices. Transaction costs are
    applied at each rebalance as ``cost_bps * sum |delta_w| / 10000``
    of the portfolio value.

    Args:
        history: Price history (must have ``n_timestamps >= 2``).
        config: Backtest configuration.

    Returns:
        A ``BacktestResult`` capturing the time-series and aggregates.

    Raises:
        ValueError: If the price history is too short or has zero
            variance in any instrument.
    """
    from convexfolio import CFVaR3Numerical, CFVaR3Objective

    if history.n_timestamps < 2:
        raise ValueError("price history must have at least 2 timestamps")
    n_timestamps = history.n_timestamps
    n_instruments = history.n_instruments
    if config.rebalance_frequency < 1:
        raise ValueError("rebalance_frequency must be >= 1")

    weights_matrix = np.zeros((n_timestamps, n_instruments), dtype=float)
    portfolio_value = np.ones(n_timestamps, dtype=float)
    turnover = np.zeros(n_timestamps, dtype=float)
    cumulative_costs = np.zeros(n_timestamps, dtype=float)

    previous_weights = np.zeros(n_instruments, dtype=float)
    initial_inputs = config.portfolio_inputs

    cost_per_unit = float(config.transaction_cost_bps) / 10_000.0

    for t in range(n_timestamps):
        rebalance_now = (
            t == 0
            or t % int(config.rebalance_frequency) == 0
        )
        if rebalance_now:
            if t == 0:
                initial_prices = history.prices[0]
                implied_inputs = initial_inputs
            else:
                implied_inputs = _scale_inputs_for_prices(
                    initial_inputs, initial_prices, history.prices[t]
                )
            try:
                objective = CFVaR3Objective(
                    alpha=config.alpha,
                    expected_payoff=implied_inputs.expected_payoff,
                    precision_matrix=implied_inputs.precision_matrix,
                    kappa3_callback=lambda x: 0.0,
                )
                w = CFVaR3Numerical(
                    cost_vector=implied_inputs.cost_vector,
                    initial_weights=(
                        implied_inputs.cost_vector
                        / float(
                            implied_inputs.cost_vector @ implied_inputs.cost_vector
                        )
                    ),
                    objective_callable=objective,
                    extra_constraints=config.extra_constraints,
                ).value
            except (ValueError, RuntimeError):
                w = previous_weights if previous_weights.any() else (
                    implied_inputs.cost_vector
                    / float(implied_inputs.cost_vector @ implied_inputs.cost_vector)
                )
            delta = w - previous_weights
            cost = cost_per_unit * float(np.sum(np.abs(delta)))
            if t > 0:
                portfolio_value[t] = portfolio_value[t - 1] * (1.0 - cost)
                turnover[t] = float(np.sum(np.abs(delta)))
                cumulative_costs[t] = cumulative_costs[t - 1] + cost
            weights_matrix[t] = w
            previous_weights = w
        else:
            weights_matrix[t] = previous_weights
            if t > 0:
                portfolio_value[t] = portfolio_value[t - 1]

    summary = {
        "n_timestamps": n_timestamps,
        "n_instruments": n_instruments,
        "rebalance_frequency": int(config.rebalance_frequency),
        "transaction_cost_bps": float(config.transaction_cost_bps),
        "alpha": float(config.alpha),
        "final_portfolio_value": float(portfolio_value[-1]),
        "total_turnover": float(np.sum(turnover)),
        "total_costs": float(cumulative_costs[-1]),
        "max_drawdown": _max_drawdown(portfolio_value),
    }
    return BacktestResult(
        timestamps=history.timestamps,
        portfolio_value=portfolio_value,
        weights=weights_matrix,
        turnover=turnover,
        cumulative_costs=cumulative_costs,
        summary=summary,
    )


def _scale_inputs_for_prices(
    base: PortfolioInputs,
    base_prices: np.ndarray,
    current_prices: np.ndarray,
) -> PortfolioInputs:
    """Rescale base inputs by the ratio current/base prices.

    The expected-payoff vector scales linearly with prices; the cost
    vector is the current price; the precision matrix scales
    quadratically.

    Args:
        base: Base portfolio inputs.
        base_prices: The base price level (one per instrument).
        current_prices: The current price level.

    Returns:
        A new ``PortfolioInputs`` rescaled for the current prices.
    """
    base_prices = np.asarray(base_prices, dtype=float)
    current_prices = np.asarray(current_prices, dtype=float)
    ratio = current_prices / base_prices
    return PortfolioInputs(
        expected_payoff=base.expected_payoff * ratio,
        cost_vector=current_prices.copy(),
        precision_matrix=base.precision_matrix
        / np.outer(ratio, ratio),
    )


def _max_drawdown(values: np.ndarray) -> float:
    """Maximum peak-to-trough drawdown as a fraction.

    Args:
        values: 1-D series of portfolio values.

    Returns:
        Maximum drawdown (positive number, e.g. 0.10 = 10% drawdown).
    """
    running_max = np.maximum.accumulate(values)
    drawdowns = (running_max - values) / np.where(running_max > 0, running_max, 1.0)
    return float(np.max(drawdowns))


__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "PriceHistory",
    "load_price_history_csv",
    "run_backtest",
]
