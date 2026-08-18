"""Command line interface for oop package consumers."""

import argparse
import json

from oop.config import load_config
from oop.determinism import deterministic_report
from oop.logging_utils import configure_logging
from oop.pipeline import run_reproduction
from oop.pipeline import save_report


def build_parser() -> argparse.ArgumentParser:
    """Builds CLI parser."""
    parser = argparse.ArgumentParser(
        prog="oop", description="Optimal option portfolio optimizer"
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
    """CLI entrypoint."""
    parser = build_parser()
    parsed_args = parser.parse_args()
    experiment = load_config(parsed_args.config)
    configure_logging(experiment.runtime.log_level)

    if parsed_args.command == "validate-determinism":
        determinism_summary = deterministic_report(
            config=experiment, repetitions=parsed_args.repetitions
        )
        print(json.dumps(determinism_summary, indent=2))
        if not determinism_summary["deterministic"]:
            raise SystemExit(2)
        return

    report = run_reproduction(experiment)
    if parsed_args.command == "reproduce-report":
        output_path = save_report(report, experiment.runtime.output_dir)
        print(str(output_path))
        return
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
