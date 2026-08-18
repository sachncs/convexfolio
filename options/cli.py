"""Command line interface for the options package."""

import argparse
import json

from options.config import load
from options.determinism import check
from options.pipeline import reproduce
from options.utils import Logger


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        prog="options", description="Optimal option portfolio optimizer"
    )
    argument_parser.add_argument(
        "--config", type=str, default=None, help="Path to JSON config file"
    )
    argument_parser.add_argument(
        "--command",
        type=str,
        default="reproduce-report",
        choices=["reproduce-report", "print-report", "validate-determinism"],
        help="Execution command",
    )
    argument_parser.add_argument(
        "--repetitions", type=int, default=3, help="Determinism repetitions"
    )
    return argument_parser


def main() -> None:
    argument_parser = parser()
    parsed_args = argument_parser.parse_args()
    experiment = load(parsed_args.config)
    log = Logger(level=experiment.runtime.log_level)

    if parsed_args.command == "validate-determinism":
        report = check(experiment, repetitions=parsed_args.repetitions)
        log.info(json.dumps(report.summary, indent=2))
        if not report.deterministic:
            raise SystemExit(2)
        return

    if parsed_args.command == "reproduce-report":
        from options.pipeline import run_and_save
        output_path = run_and_save(experiment, experiment.runtime.output_dir)
        log.info(str(output_path))
        return

    result = reproduce(experiment)
    log.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
