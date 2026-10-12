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

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from convexfolio.config import PortfolioInputs
from convexfolio.constraints import SLSQPLambda, fun_of, long_only_inequalities
from convexfolio.errors import ValidationError
from convexfolio.math import CFVaR3Numerical, CFVaR3Objective


@dataclass(frozen=True)
class PriceHistory:
    """Bundle of historical prices for a backtest.

    Attributes:
        timestamps: 1-D array of timestamp labels (string or numeric).
        prices: 2-D array of shape ``(n_timestamps, n_instruments)``.
    """

    timestamps: np.ndarray
    prices: np.ndarray

    def __post_init__(self) -> None:
        """Copy and validate timestamps and strictly positive prices."""
        timestamps = np.array(self.timestamps, copy=True)
        prices = np.array(self.prices, dtype=float, copy=True)
        if timestamps.ndim != 1 or timestamps.size == 0:
            raise ValidationError(
                "timestamps must be a non-empty one-dimensional array"
            )
        if prices.ndim != 2 or prices.shape[0] != timestamps.shape[0]:
            raise ValidationError(
                "prices must be two-dimensional with one row per timestamp"
            )
        if prices.shape[1] == 0 or not np.all(np.isfinite(prices)):
            raise ValidationError("prices must contain finite instrument values")
        if np.any(prices <= 0.0):
            raise ValidationError("prices must contain only positive values")
        object.__setattr__(self, "timestamps", timestamps)
        object.__setattr__(self, "prices", prices)

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
    input_path = Path(path)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file has no header row")
        if not header or any(not column.strip() for column in header):
            raise ValueError("CSV header must contain non-empty column names")
        if header[0] != "timestamp":
            raise ValueError(
                f"first CSV column must be 'timestamp' (got {header[0]!r})"
            )
        if len(header) < 2 or len(set(header)) != len(header):
            raise ValueError(
                "CSV header must contain unique timestamp and price columns"
            )
        timestamps: list[str] = []
        rows: list[list[float]] = []
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) != len(header):
                raise ValueError(
                    "CSV data rows must match the header column count"
                )
            if not row[0].strip():
                raise ValueError("CSV timestamp values must be non-empty")
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
        tolerate_solver_failure: When ``True``, a failed rebalance
            reuses the previous feasible weights (or a budget-feasible
            starting point on the very first failure). When ``False``
            (the default), solver failures raise :class:`RuntimeError`
            so callers see the underlying problem.
        extra_constraints: Additional SLSQP constraint dicts.
    """

    portfolio_inputs: PortfolioInputs
    rebalance_frequency: int = 1
    transaction_cost_bps: float = 5.0
    alpha: float = 0.05
    tolerate_solver_failure: bool = False
    extra_constraints: tuple[dict[str, str | SLSQPLambda], ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        """Validate simulation and solver configuration."""
        if self.rebalance_frequency < 1:
            raise ValidationError("rebalance_frequency must be >= 1")
        if (
            not np.isfinite(self.transaction_cost_bps)
            or self.transaction_cost_bps < 0.0
        ):
            raise ValidationError(
                "transaction_cost_bps must be finite and non-negative"
            )
        if not np.isfinite(self.alpha) or not 0.0 < self.alpha < 0.5:
            raise ValidationError("alpha must satisfy 0 < alpha < 0.5")


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


class BacktestEngine(ABC):
    """Interface for a configured backtest execution engine."""

    @abstractmethod
    def run(self) -> BacktestResult:
        """Run the engine and return a validated result."""


class HistoricalBacktest(BacktestEngine):
    """Concrete engine for a historical price series and configuration."""

    def __init__(self, history: PriceHistory, config: BacktestConfig) -> None:
        self.history = history
        self.config = config

    def run(self) -> BacktestResult:
        """Run the configured historical backtest."""
        return run_backtest(self.history, self.config)


def run_backtest(history: PriceHistory, config: BacktestConfig) -> BacktestResult:
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

    holdings = np.zeros(n_instruments, dtype=float)
    initial_inputs = config.portfolio_inputs

    cost_per_unit = float(config.transaction_cost_bps) / 10_000.0

    for t in range(n_timestamps):
        rebalance_now = t == 0 or t % int(config.rebalance_frequency) == 0
        current_prices = history.prices[t]
        if t == 0:
            current_value = 1.0
            current_weights = np.zeros(n_instruments, dtype=float)
        else:
            current_value = float(np.dot(holdings, current_prices))
            if not np.isfinite(current_value) or current_value <= 0.0:
                raise RuntimeError(f"portfolio value became invalid at t={t}")
            current_weights = holdings * current_prices / current_value
        if rebalance_now:
            implied_inputs = scale_inputs_for_prices(
                initial_inputs, initial_inputs.cost_vector, current_prices
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
                        / float(implied_inputs.cost_vector @ implied_inputs.cost_vector)
                    ),
                    objective_callable=objective,
                        extra_constraints=(
                            *long_only_inequalities(n_instruments),
                            *config.extra_constraints,
                        ),
                ).value
            except (ValueError, RuntimeError) as exc:
                if not config.tolerate_solver_failure:
                    raise RuntimeError(f"rebalance at t={t} failed: {exc}") from exc
                w = (
                    current_weights / current_prices
                    if t > 0
                    else np.full(n_instruments, 1.0 / n_instruments) / current_prices
                )
                if not np.isclose(float(w @ current_prices), 1.0, atol=1e-8):
                    raise RuntimeError(
                        f"fallback weights were not budget-feasible at t={t}"
                    ) from exc
                for constraint in config.extra_constraints:
                    residual = float(fun_of(constraint)(w))
                    if not np.isfinite(residual) or residual < -1e-8:
                        raise RuntimeError(
                            "fallback weights violated a configured "
                            f"constraint at t={t}"
                        ) from exc
            target_allocations = w * current_prices
            turnover_fraction = (
                float(np.sum(np.abs(target_allocations - current_weights)))
                if t > 0
                else 0.0
            )
            cost = cost_per_unit * turnover_fraction
            if cost >= 1.0:
                raise RuntimeError(f"transaction cost consumed portfolio at t={t}")
            portfolio_value[t] = current_value * (1.0 - cost)
            turnover[t] = turnover_fraction
            cumulative_costs[t] = (
                cumulative_costs[t - 1] + cost if t > 0 else 0.0
            )
            holdings = portfolio_value[t] * w
            weights_matrix[t] = w
        else:
            portfolio_value[t] = current_value
            weights_matrix[t] = current_weights

    summary = {
        "n_timestamps": n_timestamps,
        "n_instruments": n_instruments,
        "rebalance_frequency": int(config.rebalance_frequency),
        "transaction_cost_bps": float(config.transaction_cost_bps),
        "alpha": float(config.alpha),
        "final_portfolio_value": float(portfolio_value[-1]),
        "total_turnover": float(np.sum(turnover)),
        "total_costs": float(cumulative_costs[-1]),
        "max_drawdown": max_drawdown(portfolio_value),
    }
    return BacktestResult(
        timestamps=history.timestamps,
        portfolio_value=portfolio_value,
        weights=weights_matrix,
        turnover=turnover,
        cumulative_costs=cumulative_costs,
        summary=summary,
    )


def scale_inputs_for_prices(
    base: PortfolioInputs,
    base_prices: np.ndarray,
    current_prices: np.ndarray,
) -> PortfolioInputs:
    """Rescale base portfolio inputs by the ratio current/base prices.

    The expected-payoff vector scales linearly with prices; the cost
    vector becomes the current price; the precision matrix scales
    quadratically (i.e. divided by the outer product of the ratio
    vector, matching the inverse-vol interpretation of the precision
    matrix).

    Args:
        base: Base portfolio inputs.
        base_prices: The base price level (one per instrument).
        current_prices: The current price level.

    Returns:
        A new :class:`~convexfolio.config.PortfolioInputs` rescaled
        for the current prices.
    """
    base_prices = np.asarray(base_prices, dtype=float)
    current_prices = np.asarray(current_prices, dtype=float)
    if (
        base_prices.ndim != 1
        or current_prices.shape != base_prices.shape
        or base_prices.shape != base.cost_vector.shape
    ):
        raise ValidationError("price vectors must match the portfolio dimensions")
    if not np.all(np.isfinite(base_prices)) or not np.all(np.isfinite(current_prices)):
        raise ValidationError("price vectors must contain only finite values")
    if np.any(base_prices <= 0.0) or np.any(current_prices <= 0.0):
        raise ValidationError("price vectors must contain only positive values")
    ratio = current_prices / base_prices
    return PortfolioInputs(
        expected_payoff=base.expected_payoff * ratio,
        cost_vector=current_prices.copy(),
        precision_matrix=base.precision_matrix / np.outer(ratio, ratio),
    )


def max_drawdown(values: np.ndarray) -> float:
    """Maximum peak-to-trough drawdown as a fraction.

    Args:
        values: 1-D series of portfolio values.

    Returns:
        Maximum drawdown (positive number, e.g. ``0.10`` means a 10%
        peak-to-trough loss).
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
