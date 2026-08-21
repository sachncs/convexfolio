"""ETL bridge between the SP500 options-IV HuggingFace dataset and Convexfolio.

This module turns the rows of ``gauss314/options-IV-SP500`` into
:class:`~convexfolio.config.PortfolioInputs` instances and threads them
through the closed-form variance minimiser. It is organised as five
pipeline stages — Extract, Parse, Transform, Solve, Summarise — wired
together by the :class:`CrossSectionRunner` orchestrator.

Public surface:

* **Extract** — :class:`HFDatasetSource` and :class:`CSVFileSource`,
  two duck-typed sources that yield raw row dicts.
* **Parse** — :class:`Parse`, a stateless class that turns
  one raw dict into a validated :class:`OptionsRow`. Called as
  ``Parse(row) -> OptionsRow``.
* **Transform** — :class:`BuildPortfolioInputs`, a configurable
  composition class with two state parameters
  (``off_diagonal_correlation`` and ``realised_vol_window``).
* **Solve** — no wrapper. Callers use
  :class:`~convexfolio.math.Minimize` and
  :class:`~convexfolio.math.Variance` directly.
* **Summarise** — :class:`SummariseResults`, a streaming Welford
  accumulator.
* **Orchestrate** — :class:`LoadOptionsIV` (composes a source with a
  parser) and :class:`CrossSectionRunner` (composes the loader with a
  builder and a summariser).

The :mod:`datasets` package is never imported at module load time.
Installing ``convexfolio[hf-data]`` is required only when constructing
an :class:`HFDatasetSource`.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from datasets import load_dataset

from convexfolio.config import PortfolioInputs
from convexfolio.math import Minimize, Variance
from convexfolio.types import FloatArray

IV_BUCKETS: tuple[str, ...] = (
    "DITM_IV",
    "ITM_IV",
    "sITM_IV",
    "ATM_IV",
    "sOTM_IV",
    "OTM_IV",
    "DOTM_IV",
)

HV_COLUMNS: tuple[str, ...] = (
    "hv_20",
    "hv_40",
    "hv_60",
    "hv_75",
    "hv_90",
    "hv_120",
    "hv_180",
    "hv_200",
)

DATASET_REPO_ID: str = "gauss314/options-IV-SP500"
DATASET_SUBSET: str = "default"
DATASET_SPLIT: str = "train"


@dataclass(frozen=True)
class OptionsRow:
    """One validated row from the SP500 options-IV dataset.

    Attributes:
        symbol: Ticker symbol (e.g. ``"AAPL"``).
        date: ISO date string in ``YYYY-MM-DD`` format.
        iv_values: Length-7 array of moneyness-bucket implied vols,
            in :data:`IV_BUCKETS` order.
        hv_values: Length-8 array of historical vols, in
            :data:`HV_COLUMNS` order.
        vix: CBOE VIX level on that date, in percent.
    """

    symbol: str
    date: str
    iv_values: FloatArray
    hv_values: FloatArray
    vix: float


@dataclass(frozen=True)
class CrossSectionResult:
    """One ``(symbol, date)`` portfolio solution.

    Attributes:
        symbol: Ticker symbol.
        date: ISO date string in ``YYYY-MM-DD`` format.
        inputs: The :class:`~convexfolio.config.PortfolioInputs` that
            fed the solver.
        weights: Closed-form optimal weights from
            :class:`~convexfolio.math.Minimize`.
    """

    symbol: str
    date: str
    inputs: PortfolioInputs
    weights: FloatArray


class BucketWeightStat(TypedDict):
    """Per-bucket weight statistics from :class:`SummariseResults`.

    Attributes:
        bucket: IV bucket column name from :data:`IV_BUCKETS`.
        mean: Mean of the closed-form optimal weight across groups.
        std: Population standard deviation of the optimal weight.
        n: Number of groups that contributed to this bucket's stats.
    """

    bucket: str
    mean: float
    std: float
    n: int


def require_numeric(row: dict[str, Any], key: str) -> float:
    """Pull a non-NaN float from a dataset row.

    Args:
        row: The raw row dict.
        key: Column name to extract.

    Returns:
        The float value at ``row[key]``.

    Raises:
        ValueError: If the column is absent or non-finite.
    """
    value = row.get(key)
    if value is None:
        raise ValueError(f"row missing column {key!r}")
    value_float = float(value)
    if not math.isfinite(value_float):
        raise ValueError(f"row has non-finite value in column {key!r}")
    return value_float


class Parse:
    """Parse one raw dataset row dict into an :class:`OptionsRow`.

    Callable: ``Parse(row)`` returns the parsed :class:`OptionsRow`
    directly (no state, no instance needed).

    Args:
        row: A single row from the dataset, with string keys and
            scalar values.

    Returns:
        The parsed :class:`OptionsRow`.

    Raises:
        ValueError: If ``symbol`` or ``date`` is missing/empty, or if
            any column in :data:`IV_BUCKETS`, :data:`HV_COLUMNS`, or
            ``VIX`` is missing or non-finite.
    """

    def __new__(  # type: ignore[misc]
        cls, row: dict[str, Any]
    ) -> OptionsRow:
        symbol = str(row.get("symbol", "")).strip()
        date = str(row.get("date", "")).strip()
        if not symbol:
            raise ValueError("row missing 'symbol'")
        if not date:
            raise ValueError("row missing 'date'")
        iv_values = np.array(
            [require_numeric(row, key) for key in IV_BUCKETS], dtype=float
        )
        hv_values = np.array(
            [require_numeric(row, key) for key in HV_COLUMNS], dtype=float
        )
        vix = require_numeric(row, "VIX")
        return OptionsRow(
            symbol=symbol,
            date=date,
            iv_values=iv_values,
            hv_values=hv_values,
            vix=vix,
        )


class HFDatasetSource:
    """Yield raw row dicts from a HuggingFace dataset (Extract stage).

    Lazy: the :mod:`datasets` package is only imported on the first
    call to :meth:`__iter__`. Install ``convexfolio[hf-data]`` to
    enable this path.

    Args:
        repo_id: HuggingFace dataset repository id. Defaults to
            :data:`DATASET_REPO_ID`.
        subset: Config / subset name. Defaults to
            :data:`DATASET_SUBSET`.
        split: Split name. Defaults to :data:`DATASET_SPLIT`.
        streaming: If ``True`` (default), stream rows from the Hub
            without downloading the full parquet file. Set to
            ``False`` to materialise the table locally first.
        symbols: Optional whitelist of ticker symbols to keep.
        max_rows: Optional cap on the number of rows yielded.

    Attributes:
        repo_id: See Args.
        subset: See Args.
        split: See Args.
        streaming: See Args.
        symbols: See Args.
        max_rows: See Args.
    """

    def __init__(
        self,
        repo_id: str = DATASET_REPO_ID,
        subset: str = DATASET_SUBSET,
        split: str = DATASET_SPLIT,
        streaming: bool = True,
        symbols: Iterable[str] | None = None,
        max_rows: int | None = None,
    ) -> None:
        self.repo_id = repo_id
        self.subset = subset
        self.split = split
        self.streaming = streaming
        self.symbols = frozenset(symbols) if symbols is not None else None
        self.max_rows = max_rows

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield raw row dicts, honouring the symbol whitelist and cap.

        Yields:
            Raw row dicts as returned by the Hub.
        """
        dataset = load_dataset(
            self.repo_id,
            self.subset,
            split=self.split,
            streaming=self.streaming,
        )
        count = 0
        for raw in dataset:
            symbol_value = str(raw.get("symbol", "")).strip()
            if self.symbols is not None and symbol_value not in self.symbols:
                continue
            yield dict(raw)
            count += 1
            if self.max_rows is not None and count >= self.max_rows:
                return


class CSVFileSource:
    """Yield raw row dicts from a local CSV file (Extract stage).

    Args:
        path: Path to a CSV file with the SP500 options-IV dataset's
            column layout.

    Attributes:
        path: See Args.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Yield raw row dicts from the CSV.

        Yields:
            One dict per non-empty row, keyed by the CSV header.

        Raises:
            FileNotFoundError: If :attr:`path` does not exist.
            ValueError: If the CSV has no header row.
        """
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("CSV file has no header row")
            for raw in reader:
                yield dict(raw)


class LoadOptionsIV:
    """Iterate parsed :class:`OptionsRow` instances from a source.

    Composition: holds a source (any duck-typed iterable of dicts)
    and a parser. Each call to :meth:`__iter__` yields one parsed
    row per source element.

    Args:
        source: Any object that yields raw row dicts when iterated.
            Both :class:`HFDatasetSource` and :class:`CSVFileSource`
            satisfy this protocol via duck typing.
        parser: Callable turning one raw dict into an
            :class:`OptionsRow`. Defaults to :class:`Parse`.

    Attributes:
        source: See Args.
        parser: See Args.
    """

    def __init__(
        self,
        source: Iterable[dict[str, Any]],
        parser: Any = Parse,
    ) -> None:
        self.source = source
        self.parser = parser

    def __iter__(self) -> Iterator[OptionsRow]:
        """Yield parsed :class:`OptionsRow` instances.

        Yields:
            :class:`OptionsRow` for each source element.
        """
        for raw in self.source:
            yield self.parser(raw)


class BuildPortfolioInputs:
    """Build a :class:`PortfolioInputs` from one :class:`OptionsRow`.

    Holds two configurable parameters previously hardcoded inside the
    free function: the off-diagonal correlation factor used in the
    precision matrix, and the historical-vol aggregation used as the
    realised-vol proxy.

    Args:
        off_diagonal_correlation: Scalar in ``[0, 1]`` mixing the
            inverse-vol diagonal with the cross-product outer term.
            ``0.0`` → fully diagonal precision; ``1.0`` → full
            correlation. Default ``0.1`` matches the convention in
            :func:`convexfolio.data.load_csv`.
        realised_vol_window: ``"median"`` or ``"mean"`` of the row's
            ``hv_values``. Default ``"median"`` (robust to a single
            noisy window).

    Attributes:
        off_diagonal_correlation: See Args.
        realised_vol_window: See Args.

    Raises:
        ValueError: If ``off_diagonal_correlation`` is outside
            ``[0, 1]`` or ``realised_vol_window`` is not a recognised
            aggregation name.
    """

    def __init__(
        self,
        off_diagonal_correlation: float = 0.1,
        realised_vol_window: str = "median",
    ) -> None:
        if not 0.0 <= off_diagonal_correlation <= 1.0:
            raise ValueError(
                f"off_diagonal_correlation must be in [0, 1]; got "
                f"{off_diagonal_correlation}"
            )
        if realised_vol_window not in {"median", "mean"}:
            raise ValueError(
                f"realised_vol_window must be 'median' or 'mean'; got "
                f"{realised_vol_window!r}"
            )
        self.off_diagonal_correlation = off_diagonal_correlation
        self.realised_vol_window = realised_vol_window

    def __call__(self, row: OptionsRow) -> PortfolioInputs:
        """Build portfolio inputs from one row.

        Mappings (see paper §2.4):

        * ``cost_vector`` — the seven IVs themselves (option price is
          monotone in IV for a fixed moneyness).
        * ``expected_payoff`` — mean-reversion signal; positive means
          the IV bucket is *cheaper* than its row-average peer, i.e.
          a long-vol candidate.
        * ``precision_matrix`` — diagonal of inverse-vol precision
          with the configured off-diagonal correlation.

        Args:
            row: A parsed :class:`OptionsRow`.

        Returns:
            A :class:`~convexfolio.config.PortfolioInputs` ready for
            the solver.

        Raises:
            ValueError: If the IV vector is not length 7, contains
                non-finite values, or contains non-positive entries.
        """
        iv_values = np.asarray(row.iv_values, dtype=float)
        if iv_values.ndim != 1 or iv_values.shape[0] != len(IV_BUCKETS):
            raise ValueError(
                f"iv_values must be length {len(IV_BUCKETS)}; got {iv_values.shape}"
            )
        if not np.all(np.isfinite(iv_values)) or np.any(iv_values <= 0.0):
            raise ValueError("iv_values must be finite and strictly positive")

        realised_vol = self.realised_vol(np.asarray(row.hv_values, dtype=float))
        if not math.isfinite(realised_vol) or realised_vol <= 0.0:
            realised_vol = 1.0

        cost_vector = iv_values
        iv_mean = float(iv_values.mean())
        expected_payoff = -(iv_values - iv_mean) / iv_mean
        precision_matrix = self.precision_matrix(iv_values, realised_vol)
        return PortfolioInputs(
            expected_payoff=expected_payoff,
            cost_vector=cost_vector,
            precision_matrix=precision_matrix,
        )

    def realised_vol(self, hv_values: FloatArray) -> float:
        """Aggregate a row's historical-vol windows into a single proxy.

        Args:
            hv_values: 1-D array of historical vols across the
                :data:`HV_COLUMNS` windows.

        Returns:
            The aggregated realised-vol proxy (median or mean of
            ``hv_values``).
        """
        if self.realised_vol_window == "median":
            return float(np.median(hv_values))
        return float(np.mean(hv_values))

    def precision_matrix(
        self, iv_values: FloatArray, realised_vol: float
    ) -> FloatArray:
        """Build a 7×7 precision matrix from IVs and a realised-vol proxy.

        The diagonal carries ``1 / (iv * realised_vol)`` — cheaper
        and less volatile instruments receive less precision weight.
        Off-diagonal entries are scaled by
        :attr:`off_diagonal_correlation`.

        Args:
            iv_values: 1-D IV array of length 7.
            realised_vol: Realised-vol proxy from
                :meth:`realised_vol`.

        Returns:
            The 7×7 symmetric precision matrix.
        """
        diag = 1.0 / np.maximum(iv_values * realised_vol, 1e-6)
        outer = np.outer(diag, diag) ** 0.5
        outer = outer + np.diag(diag - outer.diagonal())
        return (
            self.off_diagonal_correlation * outer
            + (1.0 - self.off_diagonal_correlation) * np.diag(diag)
        )


class SummariseResults:
    """Streaming Welford accumulator for a cross-sectional run.

    Updates with one :class:`CrossSectionResult` at a time; finalise
    returns a JSON-serialisable summary. Memory-bounded: O(buckets)
    regardless of how many results are ingested.

    Attributes:
        n_groups: Number of :meth:`update` calls seen so far.
        n_unique_symbols: Number of distinct symbols seen so far.
        date_min: Earliest date seen so far (``None`` until first
            update).
        date_max: Latest date seen so far (``None`` until first
            update).
    """

    def __init__(self) -> None:
        self.n_groups: int = 0
        self.n_unique_symbols: int = 0
        self.date_min: str | None = None
        self.date_max: str | None = None
        self.symbol_counts: dict[str, int] = {}
        self.bucket_count: list[int] = [0 for _ in IV_BUCKETS]
        self.bucket_mean: list[float] = [0.0 for _ in IV_BUCKETS]
        self.bucket_m2: list[float] = [0.0 for _ in IV_BUCKETS]

    def update(self, result: CrossSectionResult) -> None:
        """Incorporate one result into the running statistics.

        Args:
            result: A :class:`CrossSectionResult` from the solver.
        """
        self.n_groups += 1
        symbol = result.symbol
        self.symbol_counts[symbol] = self.symbol_counts.get(symbol, 0) + 1
        if self.date_min is None or result.date < self.date_min:
            self.date_min = result.date
        if self.date_max is None or result.date > self.date_max:
            self.date_max = result.date
        weights = np.asarray(result.weights, dtype=float).ravel()
        if weights.shape[0] != len(IV_BUCKETS):
            return
        for index, value in enumerate(weights):
            value_float = float(value)
            self.bucket_count[index] += 1
            count_for_bucket = self.bucket_count[index]
            delta = value_float - self.bucket_mean[index]
            self.bucket_mean[index] += delta / count_for_bucket
            delta2 = value_float - self.bucket_mean[index]
            self.bucket_m2[index] += delta * delta2
        self.n_unique_symbols = len(self.symbol_counts)

    def finalise(self) -> dict[str, Any]:
        """Return the JSON-serialisable summary dict.

        Returns:
            A dict with keys ``n_groups``, ``n_unique_symbols``,
            ``top_symbols``, ``date_min``, ``date_max``, and
            ``weight_stats`` (mean / std / n per IV bucket).
        """
        bucket_stats: list[BucketWeightStat] = []
        for index, bucket in enumerate(IV_BUCKETS):
            count_for_bucket = self.bucket_count[index]
            if count_for_bucket == 0:
                bucket_stats.append(
                    BucketWeightStat(bucket=bucket, mean=0.0, std=0.0, n=0)
                )
            elif count_for_bucket == 1:
                bucket_stats.append(
                    BucketWeightStat(
                        bucket=bucket,
                        mean=float(self.bucket_mean[index]),
                        std=0.0,
                        n=1,
                    )
                )
            else:
                variance = self.bucket_m2[index] / count_for_bucket
                bucket_stats.append(
                    BucketWeightStat(
                        bucket=bucket,
                        mean=float(self.bucket_mean[index]),
                        std=float(math.sqrt(variance)),
                        n=count_for_bucket,
                    )
                )

        top_symbols = sorted(
            self.symbol_counts.items(), key=lambda item: item[1], reverse=True
        )[:10]

        return {
            "n_groups": self.n_groups,
            "n_unique_symbols": self.n_unique_symbols,
            "top_symbols": [
                {"symbol": symbol, "count": count_value}
                for symbol, count_value in top_symbols
            ],
            "date_min": self.date_min,
            "date_max": self.date_max,
            "weight_stats": bucket_stats,
        }


class CrossSectionRunner:
    """End-to-end cross-sectional experiment pipeline.

    Composition: holds a :class:`LoadOptionsIV`, a
    :class:`BuildPortfolioInputs`, and a :class:`SummariseResults`.
    The :meth:`run` method threads them: load row → build inputs →
    solve with :class:`~convexfolio.math.Minimize` and
    :class:`~convexfolio.math.Variance` → update the summariser →
    return the finalised summary dict.

    Args:
        loader: Row iterator source (e.g.
            ``LoadOptionsIV(HFDatasetSource(...), parse_options_row)``).
        builder: Row → :class:`~convexfolio.config.PortfolioInputs`
            builder.
        summariser: Streaming accumulator. Defaults to a fresh
            :class:`SummariseResults`.

    Attributes:
        loader: See Args.
        builder: See Args.
        summariser: See Args.
    """

    def __init__(
        self,
        loader: LoadOptionsIV,
        builder: BuildPortfolioInputs,
        summariser: SummariseResults | None = None,
    ) -> None:
        self.loader = loader
        self.builder = builder
        self.summariser = (
            summariser if summariser is not None else SummariseResults()
        )

    def run(self) -> dict[str, Any]:
        """Run the full pipeline; return the summarised result dict.

        Returns:
            The finalised summary dict from
            :meth:`SummariseResults.finalise`. Rows that raise during
            parsing or solving are skipped silently.
        """
        for row in self.loader:
            try:
                inputs = self.builder(row)
            except ValueError:
                continue
            weights = Minimize(
                Variance(inputs.precision_matrix), inputs.cost_vector
            ).value
            self.summariser.update(
                CrossSectionResult(
                    symbol=row.symbol,
                    date=row.date,
                    inputs=inputs,
                    weights=weights,
                )
            )
        return self.summariser.finalise()


__all__ = [
    "BucketWeightStat",
    "BuildPortfolioInputs",
    "CSVFileSource",
    "CrossSectionResult",
    "CrossSectionRunner",
    "DATASET_REPO_ID",
    "DATASET_SUBSET",
    "DATASET_SPLIT",
    "HFDatasetSource",
    "HV_COLUMNS",
    "IV_BUCKETS",
    "LoadOptionsIV",
    "OptionsRow",
    "Parse",
    "SummariseResults",
]
