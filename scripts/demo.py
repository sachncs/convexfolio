"""Minimal end-to-end usage demo for optimization objectives."""

from options.config import ExperimentConfig
from options.pipeline import run_reproduction


def main() -> None:
    report = run_reproduction(ExperimentConfig())
    print(report["outputs"])


if __name__ == "__main__":
    main()
