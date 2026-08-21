"""Tests for the SP500 options-IV HuggingFace data integration.

These tests never hit the network. They exercise the offline
:class:`CSVFileSource` path against a tiny CSV fixture with the same
column layout as ``gauss314/options-IV-SP500``, then drive each
class in the ETL pipeline:

* :class:`LoadOptionsIV` (composition of source + parser)
* :class:`BuildPortfolioInputs` (transform stage)
* :class:`SummariseResults` (Welford streaming accumulator)
* :class:`CrossSectionRunner` (full end-to-end)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from convexfolio import (
    HV_COLUMNS,
    IV_BUCKETS,
    BuildPortfolioInputs,
    CrossSectionRunner,
    CSVFileSource,
    HFDatasetSource,
    LoadOptionsIV,
    OptionsRow,
    SummariseResults,
    parse_options_row,
)
from convexfolio.math import Minimize, Variance

FIXTURE_PATH = "tests/fixtures/sp500_iv_sample.csv"


def test_iv_buckets_and_hv_columns_lengths() -> None:
    """The dataset's bucket and window column lists are pinned."""
    assert len(IV_BUCKETS) == 7
    assert len(HV_COLUMNS) == 8


def test_parse_options_row_extracts_arrays() -> None:
    """Raw dict → OptionsRow preserves all columns."""
    raw = {
        "symbol": "AAPL",
        "date": "2019-10-14",
        "DITM_IV": 28.23,
        "ITM_IV": 26.84,
        "sITM_IV": 25.95,
        "ATM_IV": 26.43,
        "sOTM_IV": 27.28,
        "OTM_IV": 28.48,
        "DOTM_IV": 30.21,
        "hv_20": 21.332,
        "hv_40": 24.625,
        "hv_60": 27.967,
        "hv_75": 25.931,
        "hv_90": 24.966,
        "hv_120": 27.164,
        "hv_180": 25.58,
        "hv_200": 30.27,
        "VIX": 14.57,
    }
    row = parse_options_row(raw)
    assert isinstance(row, OptionsRow)
    assert row.symbol == "AAPL"
    assert row.date == "2019-10-14"
    assert row.iv_values.shape == (7,)
    assert row.hv_values.shape == (8,)
    assert row.vix == 14.57


def test_parse_options_row_rejects_missing_symbol() -> None:
    """Missing 'symbol' raises a typed ValueError."""
    raw = {"date": "2019-10-14", "VIX": 14.57}
    with pytest.raises(ValueError, match="missing 'symbol'"):
        parse_options_row(raw)


def test_parse_options_row_rejects_non_finite() -> None:
    """NaN IV raises a typed ValueError."""
    raw = {
        "symbol": "X",
        "date": "2019-10-14",
        "DITM_IV": float("nan"),
        "ITM_IV": 1.0,
        "sITM_IV": 1.0,
        "ATM_IV": 1.0,
        "sOTM_IV": 1.0,
        "OTM_IV": 1.0,
        "DOTM_IV": 1.0,
        "hv_20": 1.0,
        "hv_40": 1.0,
        "hv_60": 1.0,
        "hv_75": 1.0,
        "hv_90": 1.0,
        "hv_120": 1.0,
        "hv_180": 1.0,
        "hv_200": 1.0,
        "VIX": 1.0,
    }
    with pytest.raises(ValueError, match="non-finite"):
        parse_options_row(raw)


def test_csv_file_source_yields_raw_dicts() -> None:
    """CSVFileSource yields one dict per data row."""
    rows = list(CSVFileSource(FIXTURE_PATH))
    assert len(rows) == 4
    assert {row["symbol"] for row in rows} == {"AAPL", "MSFT"}


def test_csv_file_source_missing_file_raises() -> None:
    """Missing CSV raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        list(CSVFileSource("/nonexistent/path.csv"))


def test_csv_file_source_missing_columns_raises(tmp_path: Path) -> None:
    """CSV without required columns raises ValueError on first row."""
    bad = tmp_path / "bad.csv"
    bad.write_text("symbol,date\nAAPL,2019-10-14\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing column"):
        list(LoadOptionsIV(CSVFileSource(bad)))


def test_load_options_iv_composes_source_and_parser() -> None:
    """LoadOptionsIV iterates parsed OptionsRow from a source."""
    rows = list(LoadOptionsIV(CSVFileSource(FIXTURE_PATH)))
    assert len(rows) == 4
    assert {row.symbol for row in rows} == {"AAPL", "MSFT"}
    assert {row.date for row in rows} == {"2019-10-14", "2019-10-15"}
    for row in rows:
        assert isinstance(row, OptionsRow)


def test_build_portfolio_inputs_shapes() -> None:
    """Builder outputs 7-vector / 7×7 arrays."""
    rows = list(LoadOptionsIV(CSVFileSource(FIXTURE_PATH)))
    builder = BuildPortfolioInputs()
    inputs = builder(rows[0])
    assert inputs.n_instruments == 7
    assert inputs.expected_payoff.shape == (7,)
    assert inputs.cost_vector.shape == (7,)
    assert inputs.precision_matrix.shape == (7, 7)


def test_build_portfolio_inputs_rejects_non_positive_iv() -> None:
    """Builder raises on IV vector containing non-positive entries."""
    rows = list(LoadOptionsIV(CSVFileSource(FIXTURE_PATH)))
    broken = OptionsRow(
        symbol=rows[0].symbol,
        date=rows[0].date,
        iv_values=np.array(
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -0.1], dtype=float
        ),
        hv_values=rows[0].hv_values,
        vix=rows[0].vix,
    )
    builder = BuildPortfolioInputs()
    with pytest.raises(ValueError, match="strictly positive"):
        builder(broken)


def test_build_portfolio_inputs_rejects_invalid_correlation() -> None:
    """Builder __init__ validates off_diagonal_correlation bounds."""
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        BuildPortfolioInputs(off_diagonal_correlation=1.5)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        BuildPortfolioInputs(off_diagonal_correlation=-0.1)


def test_build_portfolio_inputs_rejects_invalid_window() -> None:
    """Builder __init__ validates realised_vol_window choice."""
    with pytest.raises(ValueError, match="'median' or 'mean'"):
        BuildPortfolioInputs(realised_vol_window="mode")


def test_build_portfolio_inputs_satisfies_budget_constraint() -> None:
    """Builder output, fed into Minimize(Variance(...), c), satisfies c·x = 1."""
    rows = list(LoadOptionsIV(CSVFileSource(FIXTURE_PATH)))
    builder = BuildPortfolioInputs()
    inputs = builder(rows[0])
    weights = Minimize(
        Variance(inputs.precision_matrix), inputs.cost_vector
    ).value
    assert np.isclose(
        float(weights.T @ inputs.cost_vector), 1.0, atol=1e-8
    )


def test_summarise_results_welford_matches_naive_two_pass() -> None:
    """Welford streaming stats equal numpy's two-pass reference."""
    rows = list(LoadOptionsIV(CSVFileSource(FIXTURE_PATH)))
    builder = BuildPortfolioInputs()
    summariser = SummariseResults()

    weight_columns: list[list[float]] = [[] for _ in IV_BUCKETS]
    for row in rows:
        try:
            inputs = builder(row)
        except ValueError:
            continue
        weights = Minimize(
            Variance(inputs.precision_matrix), inputs.cost_vector
        ).value
        from convexfolio.hf_data import CrossSectionResult

        summariser.update(
            CrossSectionResult(
                symbol=row.symbol,
                date=row.date,
                inputs=inputs,
                weights=weights,
            )
        )
        for index, value in enumerate(np.asarray(weights).ravel()):
            weight_columns[index].append(float(value))

    summary = summariser.finalise()
    json.dumps(summary)  # must not raise
    assert summary["n_groups"] == 4
    assert summary["n_unique_symbols"] == 2
    assert {entry["symbol"] for entry in summary["top_symbols"]} == {
        "AAPL",
        "MSFT",
    }
    assert summary["date_min"] == "2019-10-14"
    assert summary["date_max"] == "2019-10-15"
    assert len(summary["weight_stats"]) == 7

    for index, stat in enumerate(summary["weight_stats"]):
        column = np.asarray(weight_columns[index], dtype=float)
        if column.size < 2:
            assert stat["mean"] == 0.0 or stat["mean"] == pytest.approx(
                float(column.mean()), rel=1e-12
            )
        else:
            assert stat["mean"] == pytest.approx(
                float(column.mean()), rel=1e-12
            )
            assert stat["std"] == pytest.approx(
                float(column.std()), rel=1e-12
            )


def test_cross_section_runner_end_to_end() -> None:
    """Runner.run() drives the full pipeline and returns the summary dict."""
    loader = LoadOptionsIV(CSVFileSource(FIXTURE_PATH))
    runner = CrossSectionRunner(loader, BuildPortfolioInputs())
    summary = runner.run()
    json.dumps(summary)
    assert summary["n_groups"] == 4
    assert summary["n_unique_symbols"] == 2
    assert summary["date_min"] == "2019-10-14"
    assert summary["date_max"] == "2019-10-15"
    assert len(summary["weight_stats"]) == 7


def test_cross_section_runner_skips_malformed_rows() -> None:
    """Runner silently skips rows that fail the builder's validation."""
    raw_rows = list(CSVFileSource(FIXTURE_PATH))
    bad_raw = {**raw_rows[0], "symbol": "BAD", "DOTM_IV": -1.0}
    loader = LoadOptionsIV([bad_raw, *raw_rows])
    runner = CrossSectionRunner(loader, BuildPortfolioInputs())
    summary = runner.run()
    assert summary["n_groups"] == 4
    assert "BAD" not in {entry["symbol"] for entry in summary["top_symbols"]}


def test_hf_dataset_source_construction_does_not_import_datasets() -> None:
    """Constructing HFDatasetSource must not require the datasets lib."""
    source = HFDatasetSource(streaming=True, symbols=["AAPL"], max_rows=10)
    assert source.repo_id
    assert source.symbols == frozenset({"AAPL"})
    assert source.max_rows == 10
