"""Visualisation utilities for Convexfolio.

The Agg backend (headless-safe) is selected at module load so plot
generation works on servers without a display.

Three plot functions:

* :func:`efficient_frontier` — risk vs return across a sweep of alpha.
* :func:`weights` — horizontal bar chart of portfolio weights.
* :func:`cfvar_sensitivity` — CFVaR2 value vs alpha.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from convexfolio import CFVaR2Closed, CFVaR2nd
from convexfolio.types import FloatArray


def save_figure(fig: Any, output_path: str | Path) -> Path:
    """Persist a matplotlib figure to disk and close it.

    Creates parent directories as needed and resolves to an absolute
    path before saving.

    Args:
        fig: The matplotlib ``Figure`` to save.
        output_path: Destination path (relative or absolute).

    Returns:
        The resolved :class:`pathlib.Path` the figure was written to.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, bbox_inches="tight")
    plt.close(fig)
    return target


def weights(
    weight_vector: FloatArray,
    labels: list[str] | None = None,
    output_path: str | Path = "weights.png",
    title: str = "Portfolio weights",
) -> Path:
    """Render a horizontal bar chart of portfolio weights.

    Args:
        weight_vector: 1-D array of weights.
        labels: Optional list of instrument names.
        output_path: File to write the PNG to.
        title: Plot title.

    Returns:
        The resolved output path.
    """
    w = np.asarray(weight_vector, dtype=float)
    n = w.shape[0]
    if labels is None:
        labels = [f"i{i}" for i in range(n)]
    fig, ax = plt.subplots(figsize=(8.0, max(3.0, 0.4 * n)))
    y_positions = np.arange(n)
    colors = ["#2a8f4a" if v >= 0 else "#c14b4b" for v in w]
    ax.barh(y_positions, w, color=colors)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_xlabel("weight")
    ax.set_title(title)
    ax.axvline(0.0, color="#666666", linewidth=0.5)
    ax.grid(True, axis="x", linestyle=":", alpha=0.5)
    return save_figure(fig, output_path)


def efficient_frontier(
    precision_matrix: FloatArray,
    cost_vector: FloatArray,
    expected_payoff: FloatArray,
    alphas: list[float] | None = None,
    output_path: str | Path = "frontier.png",
    title: str = "Efficient frontier (CFVaR2)",
) -> Path:
    """Plot risk vs expected return for a sweep of alpha values.

    Solves CFVaR2Closed for each alpha, then plots
    ``expected_payoff @ x`` against ``-CFVaR2nd(alpha, ...)``.

    Args:
        precision_matrix: 2-D precision matrix ``Q``.
        cost_vector: 1-D cost vector ``v``.
        expected_payoff: 1-D expected payoff vector ``u``.
        alphas: List of alpha values to sweep. Defaults to a 20-point
            geometric grid from 0.01 to 0.49.
        output_path: File to write the PNG to.
        title: Plot title.

    Returns:
        The resolved output path.
    """
    if alphas is None:
        alphas = [0.01 * (1.5**i) for i in range(20) if 0.01 * (1.5**i) < 0.49]

    returns: list[float] = []
    risks: list[float] = []
    for alpha in alphas:
        try:
            weights_vec = CFVaR2Closed(
                precision_matrix=precision_matrix,
                expected_payoff=expected_payoff,
                cost_vector=cost_vector,
                alpha=alpha,
            ).value
            exp_return = float(np.dot(expected_payoff, weights_vec))
            risk = CFVaR2nd(
                alpha=alpha,
                expected_payoff=expected_payoff,
                precision_matrix=precision_matrix,
                weights=weights_vec,
            ).value
        except (ValueError, RuntimeError):
            continue
        returns.append(exp_return)
        risks.append(-risk)

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.plot(risks, returns, marker="o", color="#2a5fa5")
    ax.set_xlabel("-CFVaR2 (risk)")
    ax.set_ylabel("Expected portfolio return")
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    return save_figure(fig, output_path)


def cfvar_sensitivity(
    precision_matrix: FloatArray,
    cost_vector: FloatArray,
    expected_payoff: FloatArray,
    alphas: list[float] | None = None,
    output_path: str | Path = "cfvar_alpha.png",
    title: str = "CFVaR2 vs alpha",
) -> Path:
    """Plot the optimal CFVaR2 risk number as alpha varies.

    Args:
        precision_matrix: 2-D precision matrix ``Q``.
        cost_vector: 1-D cost vector ``v``.
        expected_payoff: 1-D expected payoff vector ``u``.
        alphas: List of alpha values to sweep. Defaults to a 30-point
            grid from 0.01 to 0.49.
        output_path: File to write the PNG to.
        title: Plot title.

    Returns:
        The resolved output path.
    """
    if alphas is None:
        alphas = list(np.linspace(0.01, 0.49, 30))

    risks: list[float] = []
    valid: list[float] = []
    for alpha in alphas:
        try:
            weights_vec = CFVaR2Closed(
                precision_matrix=precision_matrix,
                expected_payoff=expected_payoff,
                cost_vector=cost_vector,
                alpha=alpha,
            ).value
            risk = CFVaR2nd(
                alpha=alpha,
                expected_payoff=expected_payoff,
                precision_matrix=precision_matrix,
                weights=weights_vec,
            ).value
        except (ValueError, RuntimeError):
            continue
        valid.append(alpha)
        risks.append(-risk)

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.plot(valid, risks, marker="o", color="#c14b4b")
    ax.set_xlabel("alpha (caution)")
    ax.set_ylabel("-CFVaR2 (risk)")
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    return save_figure(fig, output_path)
