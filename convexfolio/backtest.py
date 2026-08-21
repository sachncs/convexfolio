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
    extra_constraints: tuple[dict[str, object], ...] = field(default_factory=tuple)


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


__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "PriceHistory",
    "load_price_history_csv",
]
