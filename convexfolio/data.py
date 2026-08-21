"""Data ingestion and synthetic-data generation for Convexfolio.

Three responsibilities:

* ``load_csv`` — read a CSV file of portfolio inputs into numpy arrays.
* ``synthetic_portfolio`` — generate a sample portfolio with realistic
  option Greeks derived from a skew-t distribution.
* ``to_config`` — convert a loaded ``PortfolioInputs`` into the JSON
  shape that ``convexfolio.config.load`` expects.

All routines are deterministic given a seed. No external dependencies
beyond numpy.

``PortfolioInputs`` is re-exported from ``convexfolio.config`` so the
public API has a single canonical class.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

from convexfolio.config import PortfolioInputs


def _summary(inputs: PortfolioInputs) -> dict[str, Any]:
    return {
        "n_instruments": inputs.n_instruments,
        "expected_payoff_range": [
            float(inputs.expected_payoff.min()),
            float(inputs.expected_payoff.max()),
        ],
        "cost_range": [
            float(inputs.cost_vector.min()),
            float(inputs.cost_vector.max()),
        ],
        "precision_trace": float(np.trace(inputs.precision_matrix)),
    }


def load_csv(path: str | Path) -> PortfolioInputs:
    """Load portfolio inputs from a CSV file.

    The file must have a header row and three columns:
    ``expected_payoff``, ``cost``, ``precision_diag``. The off-diagonal
    entries of the precision matrix are derived as
    ``0.1 * sqrt(precision_diag[i] * precision_diag[j])`` — a
    conservative correlation proxy. For full covariance control, build
    the matrix in Python and call ``PortfolioInputs(...)`` directly.

    Args:
        path: Path to a CSV file.

    Returns:
        A ``PortfolioInputs`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the header is missing required columns.
    """
    input_path = Path(path)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")
        required = {"expected_payoff", "cost", "precision_diag"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV missing required columns: {sorted(missing)}"
            )
        rows = [
            {
                "expected_payoff": float(r["expected_payoff"]),
                "cost": float(r["cost"]),
                "precision_diag": float(r["precision_diag"]),
            }
            for r in reader
        ]
    if not rows:
        raise ValueError("CSV file has no data rows")
    u = np.array([r["expected_payoff"] for r in rows], dtype=float)
    v = np.array([r["cost"] for r in rows], dtype=float)
    diag = np.array([r["precision_diag"] for r in rows], dtype=float)
    q = np.outer(diag, diag) ** 0.5
    q = q + np.diag(diag - q.diagonal())
    correlation = 0.1
    q = correlation * q + (1.0 - correlation) * np.diag(diag)
    return PortfolioInputs(
        expected_payoff=u, cost_vector=v, precision_matrix=q
    )


def synthetic_portfolio(
    n_instruments: int = 5,
    degrees_of_freedom: float = 8.0,
    seed: int = 7,
) -> PortfolioInputs:
    """Generate a sample portfolio with skew-t-derived precision.

    Args:
        n_instruments: Number of options in the portfolio.
        degrees_of_freedom: Skew-t degrees of freedom. Must be > 1.
        seed: Random seed for reproducibility.

    Returns:
        A ``PortfolioInputs`` instance.

    Raises:
        ValueError: If ``degrees_of_freedom <= 1``.
    """
    if degrees_of_freedom <= 1.0:
        raise ValueError("degrees_of_freedom must be > 1")
    rng = np.random.default_rng(seed)
    sample = rng.normal(size=(n_instruments, n_instruments))
    precision_matrix = sample.T @ sample + 0.5 * np.eye(n_instruments)
    cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
    expected_payoff = rng.normal(size=n_instruments) * (
        degrees_of_freedom / (degrees_of_freedom - 2.0)
    )
    return PortfolioInputs(
        expected_payoff=expected_payoff,
        cost_vector=cost_vector,
        precision_matrix=precision_matrix,
    )


def summary(inputs: PortfolioInputs) -> dict[str, Any]:
    """Return a JSON-serialisable summary of the portfolio shape."""
    return _summary(inputs)


def to_config(
    inputs: PortfolioInputs, output_directory: str = "artifacts"
) -> dict[str, Any]:
    """Convert a ``PortfolioInputs`` into a config dict.

    The returned dict is the shape that ``convexfolio.config.load``
    accepts — feed it via ``json.dump`` and pass ``--config`` to the CLI.

    Args:
        inputs: The portfolio inputs.
        output_directory: Directory for saved reports.

    Returns:
        A JSON-serialisable config dict.
    """
    return {
        "runtime": {
            "seed": 7,
            "log_level": "INFO",
            "output_directory": output_directory,
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


__all__ = [
    "PortfolioInputs",
    "load_csv",
    "synthetic_portfolio",
    "summary",
    "to_config",
]
