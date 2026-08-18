"""Determinism checks for production reproducibility."""

import json

from options.config import ExperimentConfig
from options.pipeline import run_reproduction


def deterministic_report(
    config: ExperimentConfig, repetitions: int = 2
) -> dict[str, object]:
    """Runs repeated reports and asserts deterministic equality.

    Same ``config`` and ``repetitions`` always produce the same summary;
    standard deterministic behaviour.
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


class Report:
    """Standard deterministic determinism check.

    Wraps ``deterministic_report`` with attribute access for the summary fields.
    """

    def __init__(self, config: ExperimentConfig, repetitions: int = 2) -> None:
        self.config = config
        self.repetitions = repetitions
        self.summary = deterministic_report(config, repetitions)

    @property
    def deterministic(self) -> bool:
        return bool(self.summary["deterministic"])

    @property
    def seed(self) -> int:
        return int(self.summary["seed"])

    @property
    def reference(self) -> dict[str, object]:
        return self.summary["reference_report"]
