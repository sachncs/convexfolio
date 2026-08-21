"""Command line interface for the Convexfolio package."""

import argparse
import json

from convexfolio.config import load
from convexfolio.data import PortfolioInputs, load_csv
from convexfolio.determinism import check
from convexfolio.pipeline import run_and_save
from convexfolio.utils import Logger, reproduce


def parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        The configured ``ArgumentParser``.
    """
    argument_parser = argparse.ArgumentParser(
        prog="convexfolio",
        description="Convexfolio — option portfolio optimizer",
    )
    argument_parser.add_argument(
        "--config", type=str, default=None, help="Path to JSON or YAML config file"
    )
    argument_parser.add_argument(
        "--command",
        type=str,
        default="reproduce-report",
        choices=[
            "reproduce-report",
            "print-report",
            "validate-determinism",
            "ingest",
        ],
        help="Execution command",
    )
    argument_parser.add_argument(
        "--repetitions", type=int, default=3, help="Determinism repetitions"
    )
    argument_parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to a CSV file (used by the 'ingest' command)",
    )
    return argument_parser


def _ingest_command(parsed_args: argparse.Namespace) -> PortfolioInputs:
    """Load a CSV file and print a JSON summary of the portfolio.

    Args:
        parsed_args: Parsed CLI arguments; uses ``--path``.

    Returns:
        The loaded ``PortfolioInputs``.
    """
    if not parsed_args.path:
        raise SystemExit("--path is required for the ingest command")
    inputs = load_csv(parsed_args.path)
    print(json.dumps(inputs.summary(), indent=2))
    return inputs


def main() -> None:
    """CLI entrypoint. Dispatches on ``--command`` and logs results."""
    parsed_args = parser().parse_args()

    if parsed_args.command == "ingest":
        _ingest_command(parsed_args)
        return

    experiment = load(parsed_args.config)
    log = Logger(level=experiment.runtime.log_level)

    if parsed_args.command == "validate-determinism":
        report = check(experiment, repetitions=parsed_args.repetitions)
        log.info(json.dumps(report.summary, indent=2))
        if not report.deterministic:
            raise SystemExit(2)
        return

    if parsed_args.command == "reproduce-report":
        output_path = run_and_save(experiment, experiment.runtime.output_directory)
        log.info(str(output_path))
        return

    result = reproduce(experiment)
    log.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
