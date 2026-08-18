"""Command line interface for options package consumers."""

import argparse
import json
import logging

from options.config import load
from options.determinism import deterministic_report
from options.logging_utils import configure_logging
from options.pipeline import run_reproduction
from options.pipeline import save_report

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="options", description="Optimal option portfolio optimizer"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to JSON config file"
    )
    parser.add_argument(
        "--command",
        type=str,
        default="reproduce-report",
        choices=["reproduce-report", "print-report", "validate-determinism"],
        help="Execution command",
    )
    parser.add_argument(
        "--repetitions", type=int, default=3, help="Determinism repetitions"
    )
    return parser


def main() -> None:
    parser = build_parser()
    parsed_args = parser.parse_args()
    experiment = load(parsed_args.config)
    configure_logging(experiment.runtime.log_level)

    if parsed_args.command == "validate-determinism":
        summary = deterministic_report(
            config=experiment, repetitions=parsed_args.repetitions
        )
        logger.info(json.dumps(summary, indent=2))
        if not summary["deterministic"]:
            raise SystemExit(2)
        return

    report = run_reproduction(experiment)
    if parsed_args.command == "reproduce-report":
        output_path = save_report(report, experiment.runtime.output_dir)
        logger.info(str(output_path))
        return
    logger.info(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
