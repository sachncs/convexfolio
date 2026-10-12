"""Tests for the convexfolio CLI entrypoint.

These tests shell out to the installed ``convexfolio`` command so
they exercise the real entrypoint, not just the Python module. The
package must be installed (``pip install -e .``) for these to find
``convexfolio`` on ``PATH``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from argparse import Namespace
from dataclasses import replace
from pathlib import Path

import pytest

from convexfolio.cli import backtest_command, ingest_command, plot_command
from convexfolio.config import Experiment, Runtime


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the installed ``convexfolio`` command and capture output.

    Args:
        *args: Arguments to pass after the program name.

    Returns:
        The completed process with stdout/stderr captured.
    """
    environment = os.environ.copy()
    executable_directory = str(Path(sys.executable).parent)
    environment["PATH"] = os.pathsep.join(
        [executable_directory, environment.get("PATH", "")]
    )
    return subprocess.run(
        ["convexfolio", *args],
        capture_output=True,
        env=environment,
        text=True,
        timeout=60,
    )


def test_cli_version_exits_zero() -> None:
    """``convexfolio --version`` exits 0 and prints the version."""
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.startswith("convexfolio ")
    version_line = result.stdout.strip()
    parts = version_line.split()
    assert len(parts) == 2
    version = parts[1]
    parts_of_version = version.split(".")
    assert len(parts_of_version) >= 2
    assert all(part.isdigit() for part in parts_of_version[:2])


def test_cli_help_exits_zero() -> None:
    """``convexfolio --help`` exits 0 and lists the version flag."""
    result = run_cli("--help")
    assert result.returncode == 0
    assert "--version" in result.stdout


def test_cli_invalid_json_config_exits_non_zero(tmp_path: Path) -> None:
    """Invalid JSON in --config produces a friendly error, not a traceback."""
    config_file = tmp_path / "bad.json"
    config_file.write_text("not valid json {", encoding="utf-8")
    result = run_cli("--config", str(config_file), "--command", "reproduce-report")
    assert result.returncode != 0
    assert "invalid json" in result.stderr.lower()
    assert "Traceback" not in result.stderr


def test_cli_invalid_yaml_config_exits_non_zero(tmp_path: Path) -> None:
    """Invalid YAML in --config produces a friendly error, not a traceback."""
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("runtime:\n  seed: [\n", encoding="utf-8")
    result = run_cli("--config", str(config_file), "--command", "reproduce-report")
    assert result.returncode != 0
    assert "yaml" in result.stderr.lower() or "scan" in result.stderr.lower()
    assert "Traceback" not in result.stderr


def test_cli_missing_config_file_exits_non_zero(tmp_path: Path) -> None:
    """A non-existent --config path exits with a friendly file-not-found message."""
    missing = tmp_path / "does_not_exist.json"
    result = run_cli("--config", str(missing), "--command", "reproduce-report")
    assert result.returncode != 0
    assert (
        "no such file" in result.stderr.lower() or "not found" in result.stderr.lower()
    )
    assert "Traceback" not in result.stderr


def test_cli_alpha_out_of_range_exits_non_zero(tmp_path: Path) -> None:
    """alpha outside (0, 0.5) produces a friendly error, not a traceback."""
    config_file = tmp_path / "bad_alpha.json"
    config_file.write_text(
        json.dumps({"optimization": {"alpha": 1.5}}), encoding="utf-8"
    )
    result = run_cli("--config", str(config_file), "--command", "reproduce-report")
    assert result.returncode != 0
    assert "alpha" in result.stderr.lower()
    assert "Traceback" not in result.stderr


def test_cli_print_report_runs() -> None:
    """`convexfolio --command print-report` exits 0 and emits JSON to stdout."""
    result = run_cli("--command", "print-report")
    assert result.returncode == 0, (
        f"stderr={result.stderr!r}, stdout={result.stdout[:500]!r}"
    )
    json.loads(result.stdout)  # must be valid JSON


def test_cli_ingest_command_returns_portfolio_inputs() -> None:
    """The programmatic ingest command uses the real CSV loader."""
    result = ingest_command(Namespace(path="tests/fixtures/sample_portfolio.csv"))
    assert result.n_instruments == 5


def test_cli_plot_weights_writes_artifact(tmp_path: Path) -> None:
    """The plotting command writes a non-empty weights image."""
    experiment = Experiment(runtime=Runtime(output_directory=str(tmp_path)))
    # Plotting requires explicit inputs; use the same deterministic fixture
    # construction as the public data loader.
    from convexfolio.data import LoadCSV

    inputs = LoadCSV("tests/fixtures/sample_portfolio.csv")()
    experiment = replace(experiment, inputs=inputs)
    outputs = plot_command(Namespace(chart="weights"), experiment)
    assert len(outputs) == 1
    assert Path(outputs[0]).stat().st_size > 0


def test_cli_backtest_command_requires_path() -> None:
    """Backtest reports a useful error when no price CSV is supplied."""
    with pytest.raises(SystemExit, match="--path is required"):
        backtest_command(
            Namespace(
                path=None,
                config=None,
                rebalance_frequency=1,
                transaction_cost_bps=5.0,
            )
        )
