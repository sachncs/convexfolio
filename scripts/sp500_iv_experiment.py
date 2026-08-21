"""End-to-end SP500 options-IV cross-sectional experiment.

Drives the :class:`CrossSectionRunner` over the HuggingFace dataset
``gauss314/options-IV-SP500`` (or a local CSV with the same column
layout) and prints the closed-form variance-minimisation summary to
stdout.

Usage:

    # network run on a small slice
    pip install convexfolio[hf-data]
    python scripts/sp500_iv_experiment.py --symbols AAPL MSFT --max-rows 200

    # offline run against a CSV fixture / snapshot
    python scripts/sp500_iv_experiment.py --csv tests/fixtures/sp500_iv_sample.csv

    # full 3.16M-row run against the Hub (downloads parquet once)
    python scripts/sp500_iv_experiment.py --no-streaming

The script prints the finalised summary dict plus wall-clock timing.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from convexfolio.hf_data import (
    BuildPortfolioInputs,
    CrossSectionRunner,
    CSVFileSource,
    HFDatasetSource,
    LoadOptionsIV,
    parse_options_row,
)


def parse_arguments() -> argparse.Namespace:
    """Build the CLI argument parser for the experiment.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="sp500_iv_experiment",
        description=(
            "Run cross-sectional convexfolio optimisation over the SP500 "
            "options-IV HuggingFace dataset."
        ),
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Optional path to a local CSV with the dataset's column layout",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=None,
        help="Optional whitelist of ticker symbols to keep",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap on the number of rows pulled from the Hub",
    )
    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming (downloads the full ~3M-row table to HF cache)",
    )
    return parser.parse_args()


def build_runner(arguments: argparse.Namespace) -> CrossSectionRunner:
    """Compose the runner from CLI arguments.

    Args:
        arguments: Parsed CLI arguments.

    Returns:
        A fully wired :class:`CrossSectionRunner`.
    """
    if arguments.csv is not None:
        source = CSVFileSource(Path(arguments.csv))
    else:
        source = HFDatasetSource(
            streaming=not arguments.no_streaming,
            symbols=arguments.symbols,
            max_rows=arguments.max_rows,
        )
    loader = LoadOptionsIV(source, parse_options_row)
    return CrossSectionRunner(loader, BuildPortfolioInputs())


def main() -> int:
    """Build the runner, run it, print the summary JSON.

    Returns:
        Process exit code: ``0`` on success.
    """
    arguments = parse_arguments()
    runner = build_runner(arguments)
    started_at = time.perf_counter()
    summary = runner.run()
    elapsed = time.perf_counter() - started_at
    n_groups = int(summary["n_groups"])
    rate = n_groups / elapsed if elapsed > 0 else float("inf")
    summary["elapsed_seconds"] = round(elapsed, 3)
    summary["rows_per_second"] = round(rate, 1)
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
