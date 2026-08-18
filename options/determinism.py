"""Determinism checks for production reproducibility."""

from options.config import Experiment
from options.pipeline import reproduce
from options.utils import Report


def check(config: Experiment, repetitions: int = 2) -> Report:
    """Runs repeated reproductions and builds a Report."""
    if repetitions < 2:
        raise ValueError("repetitions must be >= 2")
    results = [reproduce(config) for _ in range(repetitions)]
    return Report(config=config, repetitions=repetitions, results=results)
