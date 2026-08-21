"""Command-line interface for the Convexfolio package.

Single entrypoint (:func:`main`) dispatching on ``--command``. The
supported commands are:

* ``reproduce-report`` — load a config, run the pipeline, save the
  report to ``runtime.output_directory``.
* ``print-report`` — load a config, run the pipeline, print the
  report JSON to stdout.
* ``validate-determinism`` — run the pipeline ``--repetitions``
  times and assert the report is byte-identical.
* ``ingest`` — read a portfolio CSV (``--path``) and print a shape
  summary.
* ``plot`` — render one or more charts of the loaded experiment.
* ``backtest`` — run a multi-period rebalance backtest against a
  price-history CSV.

Helper functions :func:`ingest_command`, :func:`plot_command`, and
:func:`backtest_command` carry the per-command logic and are also
importable for programmatic use.
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from convexfolio import CFVaR2Closed, CFVaR2nd, Minimize, Variance
from convexfolio.backtest import (
    BacktestConfig,
    load_price_history_csv,
    run_backtest,
)
from convexfolio.config import Experiment, Load
from convexfolio.data import (
    LoadCSV,
    PortfolioInputs,
    Summary,
    SyntheticPortfolio,
)
from convexfolio.utils import Logger, Report, Reproduce


def parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        The configured :class:`argparse.ArgumentParser`. Reusable by
        embedders that want the same flag surface without invoking
        :func:`main`.
    """
    argument_parser = argparse.ArgumentParser(
        prog="convexfolio",
        description="Convexfolio — option portfolio optimizer",
    )
    argument_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a JSON or YAML config file",
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
        help="Which pipeline command to run",
    )
    argument_parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Determinism repetitions (used by 'validate-determinism')",
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
        help="Round-trip transaction cost in basis points (used by 'backtest')",
    )
    return argument_parser


def ingest_command(parsed_args: argparse.Namespace) -> PortfolioInputs:
    """Run the ``ingest`` command: load a CSV and log its summary.

    Args:
        parsed_args: Parsed CLI arguments. Must include ``--path``
            pointing to a portfolio CSV.

    Returns:
        The loaded :class:`~convexfolio.config.PortfolioInputs`.

    Raises:
        SystemExit: If ``--path`` was not provided.
    """
    log = Logger(level="INFO")
    if not parsed_args.path:
        raise SystemExit("--path is required for the ingest command")
    inputs = LoadCSV(parsed_args.path)()
    log.info(json.dumps(Summary(inputs).value, indent=2))
    return inputs


def plot_command(
    parsed_args: argparse.Namespace, experiment: Experiment
) -> list[str]:
    """Run the ``plot`` command: render chart(s) of an experiment.

    Args:
        parsed_args: Parsed CLI arguments. Uses ``--chart`` to pick
            which chart(s) to render (``all``, ``weights``,
            ``frontier``, ``sensitivity``).
        experiment: A loaded :class:`~convexfolio.config.Experiment`
            whose ``precision_matrix``, ``cost_vector``, and
            ``expected_payoff`` are needed by the chart primitives.

    Returns:
        A list of output paths written, one entry per chart rendered.
    """
    precision_matrix = experiment.precision_matrix
    cost_vector = experiment.cost_vector
    expected_payoff = experiment.expected_payoff
    output_dir = experiment.runtime.output_directory
    outputs: list[str] = []

    if parsed_args.chart in ("all", "weights"):
        weights_value = Minimize(
            Variance(precision_matrix), cost_vector
        ).value
        n = weights_value.shape[0]
        fig, ax = plt.subplots(figsize=(8.0, max(3.0, 0.4 * n)))
        y_positions = np.arange(n)
        colors = [
            "#2a8f4a" if v >= 0 else "#c14b4b" for v in weights_value
        ]
        ax.barh(y_positions, weights_value, color=colors)
        ax.set_yticks(y_positions)
        ax.set_yticklabels([f"i{i}" for i in range(n)])
        ax.set_xlabel("weight")
        ax.set_title("Portfolio weights")
        ax.axvline(0.0, color="#666666", linewidth=0.5)
        ax.grid(True, axis="x", linestyle=":", alpha=0.5)
        weights_path = Path(output_dir) / "weights.png"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(weights_path, bbox_inches="tight")
        plt.close(fig)
        outputs.append(str(weights_path))

    if parsed_args.chart in ("all", "frontier"):
        alphas = [
            0.01 * (1.5**i)
            for i in range(20)
            if 0.01 * (1.5**i) < 0.49
        ]
        frontier_returns: list[float] = []
        frontier_risks: list[float] = []
        for alpha_value in alphas:
            try:
                frontier_weights = CFVaR2Closed(
                    precision_matrix=precision_matrix,
                    expected_payoff=expected_payoff,
                    cost_vector=cost_vector,
                    alpha=alpha_value,
                ).value
                exp_return = float(np.dot(expected_payoff, frontier_weights))
                risk = CFVaR2nd(
                    alpha=alpha_value,
                    expected_payoff=expected_payoff,
                    precision_matrix=precision_matrix,
                    weights=frontier_weights,
                ).value
            except (ValueError, RuntimeError):
                continue
            frontier_returns.append(exp_return)
            frontier_risks.append(-risk)
        fig, ax = plt.subplots(figsize=(7.0, 5.0))
        ax.plot(frontier_risks, frontier_returns, marker="o", color="#2a5fa5")
        ax.set_xlabel("-CFVaR2 (risk)")
        ax.set_ylabel("Expected portfolio return")
        ax.set_title("Efficient frontier (CFVaR2)")
        ax.grid(True, linestyle=":", alpha=0.5)
        frontier_path = Path(output_dir) / "frontier.png"
        frontier_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(frontier_path, bbox_inches="tight")
        plt.close(fig)
        outputs.append(str(frontier_path))

    if parsed_args.chart in ("all", "sensitivity"):
        sensitivity_alphas = list(np.linspace(0.01, 0.49, 30))
        sensitivity_risks: list[float] = []
        sensitivity_valid: list[float] = []
        for alpha_value in sensitivity_alphas:
            try:
                sensitivity_weights = CFVaR2Closed(
                    precision_matrix=precision_matrix,
                    expected_payoff=expected_payoff,
                    cost_vector=cost_vector,
                    alpha=alpha_value,
                ).value
                risk = CFVaR2nd(
                    alpha=alpha_value,
                    expected_payoff=expected_payoff,
                    precision_matrix=precision_matrix,
                    weights=sensitivity_weights,
                ).value
            except (ValueError, RuntimeError):
                continue
            sensitivity_valid.append(alpha_value)
            sensitivity_risks.append(-risk)
        fig, ax = plt.subplots(figsize=(7.0, 5.0))
        ax.plot(
            sensitivity_valid,
            sensitivity_risks,
            marker="o",
            color="#c14b4b",
        )
        ax.set_xlabel("alpha (caution)")
        ax.set_ylabel("-CFVaR2 (risk)")
        ax.set_title("CFVaR2 vs alpha")
        ax.grid(True, linestyle=":", alpha=0.5)
        sensitivity_path = Path(output_dir) / "cfvar_alpha.png"
        sensitivity_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(sensitivity_path, bbox_inches="tight")
        plt.close(fig)
        outputs.append(str(sensitivity_path))

    return outputs

    return outputs


def backtest_command(parsed_args: argparse.Namespace) -> None:
    """Run the ``backtest`` command: multi-period rebalance backtest.

    Args:
        parsed_args: Parsed CLI arguments. Uses ``--path`` (price
            history CSV), ``--rebalance-frequency``,
            ``--transaction-cost-bps``, and optionally ``--config``
            (which must include an ``inputs`` section).

    Raises:
        SystemExit: If ``--path`` was not provided.
        AssertionError: If ``--config`` is given but the loaded
            experiment has no ``inputs`` section.
    """
    log = Logger(level="INFO")
    if not parsed_args.path:
        raise SystemExit("--path is required for the backtest command")
    history = load_price_history_csv(parsed_args.path)

    if parsed_args.config:
        experiment = Load(parsed_args.config)()
        assert experiment.inputs is not None, (
            "config file must include an 'inputs' section for backtest"
        )
        portfolio_inputs = experiment.inputs
    else:
        portfolio_inputs = SyntheticPortfolio(
            n_instruments=history.n_instruments, degrees_of_freedom=8.0, seed=7
        )()

    config = BacktestConfig(
        portfolio_inputs=portfolio_inputs,
        rebalance_frequency=parsed_args.rebalance_frequency,
        transaction_cost_bps=parsed_args.transaction_cost_bps,
        alpha=0.05,
    )
    result = run_backtest(history, config)
    log.info(json.dumps(result.summary, indent=2))


def main() -> None:
    """CLI entrypoint: parse args, dispatch on ``--command``, log results.

    Dispatch table:

    * ``ingest`` → :func:`ingest_command`
    * ``backtest`` → :func:`backtest_command`
    * ``plot`` → :func:`plot_command`
    * ``validate-determinism`` →
      :meth:`~convexfolio.utils.Report.from_reproduce`
    * ``reproduce-report`` →
      :meth:`~convexfolio.utils.Report.from_reproduce` plus
      :meth:`~convexfolio.utils.Report.save`
    * default (no match) → :class:`~convexfolio.utils.Reproduce`

    Raises:
        SystemExit: With code ``2`` if ``validate-determinism`` finds
            the pipeline output is non-deterministic. Other
            ``SystemExit`` values propagate from the helper commands
            (``--path`` missing, etc.).
    """
    parsed_args = parser().parse_args()

    if parsed_args.command == "ingest":
        ingest_command(parsed_args)
        return

    if parsed_args.command == "backtest":
        backtest_command(parsed_args)
        return

    experiment = Load(parsed_args.config)()
    log = Logger(level=experiment.runtime.log_level)

    if parsed_args.command == "plot":
        outputs = plot_command(parsed_args, experiment)
        for path in outputs:
            log.info(path)
        return

    if parsed_args.command == "validate-determinism":
        report = Report.from_reproduce(
            experiment, repetitions=parsed_args.repetitions
        )
        log.info(json.dumps(report.summary, indent=2))
        if not report.deterministic:
            raise SystemExit(2)
        return

    if parsed_args.command == "reproduce-report":
        report = Report.from_reproduce(experiment, repetitions=3)
        output_path = Path(experiment.runtime.output_directory) / "report.json"
        report.save(str(output_path))
        log.info(str(output_path))
        return

    result = Reproduce(experiment)()
    log.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
