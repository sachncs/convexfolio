"""Pipeline orchestration: save a determinism Report as JSON."""

from pathlib import Path

from options.config import Experiment
from options.determinism import check


def run_and_save(experiment: Experiment, output_dir: str) -> Path:
    """Run a determinism check and persist the resulting Report.

    Args:
        experiment: Top-level configuration.
        output_dir: Directory in which to write ``report.json``.

    Returns:
        The path to the written JSON file.
    """
    report = check(experiment, repetitions=3)
    target = Path(output_dir) / "report.json"
    return report.save(str(target))
