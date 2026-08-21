"""Data ingestion and synthetic-data generation for Convexfolio.

Three responsibilities, exposed as plain functions because they are
stateless and read-from-disk or pure-numpy:

* :func:`load_csv` — read a CSV file of portfolio inputs into numpy
  arrays and return a :class:`~convexfolio.config.PortfolioInputs`.
* :func:`synthetic_portfolio` — generate a sample portfolio with
  realistic option Greeks derived from a skew-t distribution.
* :func:`to_config` — convert a loaded ``PortfolioInputs`` into the
  JSON shape that :func:`~convexfolio.config.load` accepts.
* :func:`summary` — return a JSON-serialisable shape summary of a
  ``PortfolioInputs``.

All routines are deterministic given a seed. No external dependencies
beyond numpy.

``PortfolioInputs`` is re-exported from :mod:`convexfolio.config` so
the public API has a single canonical class.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

from convexfolio.config import PortfolioInputs


def load_csv(path: str | Path) -> PortfolioInputs:
    """Load portfolio inputs from a CSV file.

    The file must have a header row and three columns:
    ``expected_payoff``, ``cost``, ``precision_diag``. The off-diagonal
    entries of the precision matrix are derived as
    ``0.1 * sqrt(precision_diag[i] * precision_diag[j])`` — a
    conservative correlation proxy. For full covariance control, build
    the matrix in Python and instantiate ``PortfolioInputs(...)``
    directly.

    Args:
        path: Path to a CSV file on disk.

    Returns:
        A :class:`~convexfolio.config.PortfolioInputs` instance with
        ``expected_payoff``, ``cost_vector``, and ``precision_matrix``
        arrays derived from the CSV rows.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the CSV has no header row, is missing required
            columns, or has no data rows.
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
    expected_payoff = np.array(
        [r["expected_payoff"] for r in rows], dtype=float
    )
    cost_vector = np.array([r["cost"] for r in rows], dtype=float)
    diag = np.array([r["precision_diag"] for r in rows], dtype=float)
    precision_matrix = np.outer(diag, diag) ** 0.5
    precision_matrix = precision_matrix + np.diag(diag - precision_matrix.diagonal())
    correlation = 0.1
    precision_matrix = (
        correlation * precision_matrix + (1.0 - correlation) * np.diag(diag)
    )
    return PortfolioInputs(
        expected_payoff=expected_payoff,
        cost_vector=cost_vector,
        precision_matrix=precision_matrix,
    )


def synthetic_portfolio(
    n_instruments: int = 5,
    degrees_of_freedom: float = 8.0,
    seed: int = 7,
) -> PortfolioInputs:
    """Generate a sample portfolio with skew-t-derived precision.

    Args:
        n_instruments: Number of options in the portfolio. Must be
            positive.
        degrees_of_freedom: Skew-t degrees of freedom. Must be
            strictly greater than ``1.0`` for the distribution to
            have finite variance.
        seed: Random seed for reproducibility.

    Returns:
        A :class:`~convexfolio.config.PortfolioInputs` instance whose
        ``precision_matrix`` is positive-definite (an inverted random
        sample plus a small ridge).

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
    """Return a JSON-serialisable shape summary of a portfolio.

    Args:
        inputs: A :class:`~convexfolio.config.PortfolioInputs`
            instance.

    Returns:
        A dict with keys ``n_instruments``,
        ``expected_payoff_range`` (``[min, max]`` of the expected
        payoff vector), ``cost_range`` (``[min, max]`` of the cost
        vector), and ``precision_trace`` (sum of the diagonal entries
        of the precision matrix). Safe to serialise with
        :func:`json.dumps`.
    """
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


def to_config(
    inputs: PortfolioInputs, output_directory: str = "artifacts"
) -> dict[str, Any]:
    """Convert a ``PortfolioInputs`` into a config dict.

    The returned dict is the shape that
    :func:`~convexfolio.config.load` accepts — serialise it with
    :func:`json.dump` and pass via ``--config`` to the CLI.

    Args:
        inputs: The portfolio inputs to encode.
        output_directory: Directory for saved reports. Defaults to
            ``"artifacts"``.

    Returns:
        A JSON-serialisable config dict with the canonical
        ``runtime``, ``optimization``, and ``inputs`` sections.
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
