"""Determinism checks for production reproducibility."""

from options.config import Experiment
from options.utils import Report, reproduce


def check(config: Experiment, repetitions: int = 2) -> Report:
    """Run ``reproduce(config)`` repeatedly and return a ``Report``.

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
    results = [reproduce(config) for _ in range(repetitions)]
    return Report(config=config, repetitions=repetitions, results=results)
