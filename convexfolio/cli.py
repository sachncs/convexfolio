"""Command line interface for the Convexfolio package."""

import argparse
import json

from convexfolio.config import Experiment, load
from convexfolio.data import PortfolioInputs, load_csv, summary
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
            "plot",
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
    argument_parser.add_argument(
        "--chart",
        type=str,
        default="all",
        choices=["all", "weights", "frontier", "sensitivity"],
        help="Which chart(s) to render (used by the 'plot' command)",
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
    print(json.dumps(summary(inputs), indent=2))
    return inputs


def _plot_command(parsed_args: argparse.Namespace, experiment: Experiment) -> list[str]:
    """Render chart(s) for the loaded experiment.

    Args:
        parsed_args: Parsed CLI arguments; uses ``--chart``.
        experiment: Loaded ``Experiment`` config.

    Returns:
        List of output paths written.
    """
    from convexfolio.plot import (
        cfvar_sensitivity,
        efficient_frontier,
        weights,
    )

    precision_matrix = experiment.precision_matrix
    cost_vector = experiment.cost_vector
    expected_payoff = experiment.expected_payoff
    output_dir = experiment.runtime.output_directory
    outputs: list[str] = []

    if parsed_args.chart in ("all", "weights"):
        from convexfolio import Minimize, Variance

        w = Minimize(Variance(precision_matrix), cost_vector).value
        path = weights(w, output_path=f"{output_dir}/weights.png")
        outputs.append(str(path))

    if parsed_args.chart in ("all", "frontier"):
        path = efficient_frontier(
            precision_matrix,
            cost_vector,
            expected_payoff,
            output_path=f"{output_dir}/frontier.png",
        )
        outputs.append(str(path))

    if parsed_args.chart in ("all", "sensitivity"):
        path = cfvar_sensitivity(
            precision_matrix,
            cost_vector,
            expected_payoff,
            output_path=f"{output_dir}/cfvar_alpha.png",
        )
        outputs.append(str(path))

    return outputs


def main() -> None:
    """CLI entrypoint. Dispatches on ``--command`` and logs results."""
    parsed_args = parser().parse_args()

    if parsed_args.command == "ingest":
        _ingest_command(parsed_args)
        return

    experiment = load(parsed_args.config)
    log = Logger(level=experiment.runtime.log_level)

    if parsed_args.command == "plot":
        outputs = _plot_command(parsed_args, experiment)
        for path in outputs:
            log.info(path)
        return

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
