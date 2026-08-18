"""Command line interface for the options package."""

import argparse
import json

from options.config import load
from options.determinism import deterministic_report
from options.pipeline import run_reproduction
from options.pipeline import save_report
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
        summary = deterministic_report(
            config=experiment, repetitions=parsed_args.repetitions
        )
        log.info(json.dumps(summary, indent=2))
        if not summary["deterministic"]:
            raise SystemExit(2)
        return

    report = run_reproduction(experiment)
    if parsed_args.command == "reproduce-report":
        output_path = save_report(report, experiment.runtime.output_dir)
        log.info(str(output_path))
        return
    log.info(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
