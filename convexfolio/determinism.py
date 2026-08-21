"""Determinism checks for production reproducibility.

Public surface:

* :func:`parallel_threshold` — reads the ``OPTIONS_PARALLEL_THRESHOLD``
  env var with a default of ``4``. Above this repetition count
  :func:`check` switches to a process pool.
* :func:`check` — runs :class:`~convexfolio.utils.Reproduce` repeatedly
  (serially or via :class:`ProcessPoolExecutor`) and returns a
  :class:`~convexfolio.utils.Report`.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

from convexfolio.config import Experiment
from convexfolio.utils import Report, Reproduce


def parallel_threshold() -> int:
    """Return the minimum ``repetitions`` before the process pool kicks in.

    Reads the ``OPTIONS_PARALLEL_THRESHOLD`` env var; defaults to ``4``
    when unset or unparseable. Used by :func:`check` to decide between
    serial and parallel execution.

    Returns:
        Integer threshold above which parallel execution is used;
        otherwise :func:`check` runs serially.
    """
    return int(os.environ.get("OPTIONS_PARALLEL_THRESHOLD", "4"))


def check(config: Experiment, repetitions: int = 2) -> Report:
    """Run ``reproduce(config)`` repeatedly and return a ``Report``.

    Uses a process pool when ``repetitions`` exceeds
    :func:`parallel_threshold` so large portfolios can be validated
    faster.

    Args:
        config: Top-level configuration.
        repetitions: Number of repetitions. Must be ``>= 2``.

    Returns:
        The :class:`~convexfolio.utils.Report` describing whether
        runs were byte-equivalent.

    Raises:
        ValueError: If ``repetitions < 2``.
    """
    if repetitions < 2:
        raise ValueError("repetitions must be >= 2")

    if repetitions >= parallel_threshold():
        with ProcessPoolExecutor() as executor:
            results = list(
                executor.map(
                    lambda c: Reproduce(c)(), [config] * repetitions
                )
            )
    else:
        results = [Reproduce(config)() for _ in range(repetitions)]

    return Report(config=config, repetitions=repetitions, results=results)
