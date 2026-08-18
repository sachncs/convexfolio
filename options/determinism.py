"""Determinism checks for production reproducibility."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

from options.config import Experiment
from options.utils import Report, reproduce


def _parallel_threshold() -> int:
    """Minimum ``repetitions`` before we switch to a process pool.

    Returns:
        Threshold above which parallel execution is used; otherwise run serially.
    """
    return int(os.environ.get("OPTIONS_PARALLEL_THRESHOLD", "4"))


def _run_one(config: Experiment) -> dict[str, object]:
    """Run a single ``reproduce(config)`` in a worker process.

    Each worker receives the same ``config`` and produces a byte-equal result;
    the serial-sequential worker output is intentionally identical so the
    determinism check still validates bitwise reproducibility.
    """
    return reproduce(config)


def check(config: Experiment, repetitions: int = 2) -> Report:
    """Run ``reproduce(config)`` repeatedly and return a ``Report``.

    Uses a process pool when ``repetitions`` exceeds the configurable
    threshold (``OPTIONS_PARALLEL_THRESHOLD``, default 4) so large portfolios
    can be validated faster.

    Args:
        config: Top-level configuration.
        repetitions: Number of repetitions (must be ``>= 2``).

    Returns:
        The ``Report`` describing whether runs were byte-equivalent.

    Raises:
        ValueError: If ``repetitions < 2``.
    """
    if repetitions < 2:
        raise ValueError("repetitions must be >= 2")

    if repetitions >= _parallel_threshold():
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(_run_one, [config] * repetitions))
    else:
        results = [reproduce(config) for _ in range(repetitions)]

    return Report(config=config, repetitions=repetitions, results=results)
