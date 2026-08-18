"""Determinism checks for production reproducibility."""

import json

from oop.config import ExperimentConfig
from oop.pipeline import run_reproduction


def deterministic_report(
    config: ExperimentConfig, repetitions: int = 2
) -> dict[str, object]:
    """Runs repeated reports and asserts deterministic equality.

    Args:
      config: Runtime and optimization configuration.
      repetitions: Number of repeated runs.

    Returns:
      A summary dictionary including pass/fail and first report.
    """
    if repetitions < 2:
        raise ValueError("repetitions must be >= 2")

    serialized_reports: list[str] = []
    reports: list[dict[str, object]] = []
    for _ in range(repetitions):
        report = run_reproduction(config)
        reports.append(report)
        serialized_reports.append(json.dumps(report, sort_keys=True))

    all_match = all(item == serialized_reports[0] for item in serialized_reports[1:])
    return {
        "deterministic": all_match,
        "repetitions": repetitions,
        "seed": config.runtime.seed,
        "reference_report": reports[0],
    }
