"""Pipeline orchestration: derives ``reproduce()`` results into a saved Report."""

from pathlib import Path

from options.config import Experiment
from options.determinism import check


def run_and_save(experiment: Experiment, output_dir: str) -> Path:
    """Runs determinism check and saves the Report summary as JSON."""
    report = check(experiment, repetitions=3)
    target = Path(output_dir) / "report.json"
    return report.save(str(target))
