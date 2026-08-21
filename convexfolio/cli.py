"""Command line interface for the Convexfolio package."""

import argparse
import json

from convexfolio.config import Experiment, load
from convexfolio.data import (
    PortfolioInputs,
    load_csv,
    summary,
    synthetic_portfolio,
)
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
            "backtest",
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
        help="Path to a CSV file (used by 'ingest' and 'backtest' commands)",
    )
    argument_parser.add_argument(
        "--chart",
        type=str,
        default="all",
        choices=["all", "weights", "frontier", "sensitivity"],
        help="Which chart(s) to render (used by the 'plot' command)",
    )
    argument_parser.add_argument(
        "--rebalance-frequency",
        type=int,
        default=1,
        help="Rebalance every Nth timestamp (used by 'backtest')",
    )
    argument_parser.add_argument(
        "--transaction-cost-bps",
        type=float,
        default=5.0,
        help="Transaction cost in basis points (used by 'backtest')",
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

    if parsed_args.command == "backtest":
        _backtest_command(parsed_args)
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


def _backtest_command(parsed_args: argparse.Namespace) -> None:
    """Run a multi-period backtest from a price-history CSV.

    Args:
        parsed_args: Parsed CLI arguments; uses ``--path``,
            ``--rebalance-frequency``, ``--transaction-cost-bps``.
            Reads portfolio inputs from ``--config`` if provided;
            otherwise uses synthetic defaults.
    """
    from convexfolio.backtest import (
        BacktestConfig,
        load_price_history_csv,
        run_backtest,
    )

    if not parsed_args.path:
        raise SystemExit("--path is required for the backtest command")
    history = load_price_history_csv(parsed_args.path)

    if parsed_args.config:
        experiment = load(parsed_args.config)
        assert experiment.inputs is not None, (
            "config file must include an 'inputs' section for backtest"
        )
        portfolio_inputs = experiment.inputs
    else:
        portfolio_inputs = synthetic_portfolio(
            n_instruments=history.n_instruments, degrees_of_freedom=8.0, seed=7
        )

    config = BacktestConfig(
        portfolio_inputs=portfolio_inputs,
        rebalance_frequency=parsed_args.rebalance_frequency,
        transaction_cost_bps=parsed_args.transaction_cost_bps,
        alpha=0.05,
    )
    result = run_backtest(history, config)
    print(json.dumps(result.summary, indent=2))


if __name__ == "__main__":
    main()
