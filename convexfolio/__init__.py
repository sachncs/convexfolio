"""Public package API for the Convexfolio package.

The API is grouped by responsibility and exported via ``__all__``:

**Configuration** — runtime knobs and validation
    * :class:`Experiment` — top-level config dataclass
    * :class:`Runtime` — seed, log level, output directory
    * :class:`Optimization` — alpha, method, enforce-nu-greater-than-six
    * :class:`PortfolioInputs` — ``expected_payoff``, ``cost_vector``,
      ``precision_matrix`` bundle
    * :class:`Load` — load an :class:`Experiment` from JSON or YAML
    * :class:`Validate` — alpha-bounds validator (constructor raises)

**Data ingestion** — CSV and synthetic portfolios
    * :class:`LoadCSV` — read a portfolio CSV file
    * :class:`SyntheticPortfolio` — RNG-based sample portfolio
    * :class:`Summary` — JSON-serialisable shape summary

**SP500 options-IV HuggingFace integration**
    * :class:`OptionsRow` — single validated dataset row
    * :class:`CrossSectionResult` — one ``(symbol, date)`` portfolio
    * :class:`BucketWeightStat` — TypedDict for per-bucket stats
    * :class:`HFDatasetSource` — Extract stage: Hub rows
    * :class:`CSVFileSource` — Extract stage: local CSV rows
    * :class:`LoadOptionsIV` — composes source + parser
    * :class:`Parse` — Parse one raw row into :class:`OptionsRow`
    * :class:`BuildPortfolioInputs` — Transform stage
    * :class:`SummariseResults` — streaming Welford accumulator
    * :class:`CrossSectionRunner` — orchestrator
    * :data:`IV_BUCKETS`, :data:`HV_COLUMNS`,
      :data:`DATASET_REPO_ID`, :data:`DATASET_SUBSET`,
      :data:`DATASET_SPLIT` — constants

**Math** — closed-form portfolio primitives and skew-t building blocks
    * :class:`Variance`, :class:`Minimize`, :class:`CFVaR2Closed`,
      :class:`CFVaR3Numerical`, :class:`CFVaR3Objective`,
      :class:`CFVaR2nd`, :class:`CFVaR3rd`,
      :class:`OptimalEpsilon`, :class:`QualityScore`,
      :class:`Expect`, :class:`Quadratic`,
      :class:`PortfolioVariance`, :class:`Cumulant`
    * :class:`Compute`, :class:`Linear`, :class:`Curvature`,
      :class:`Bilinear`, :class:`Cross`,
      :class:`Linearize`, :class:`Reconstruct`,
      :class:`Greeks`, :class:`Loss`, :class:`Score`

**Backtest** — multi-period rebalance simulator
    * :class:`PriceHistory`, :class:`BacktestConfig`,
      :class:`BacktestResult` — dataclasses
    * :func:`load_price_history_csv`, :func:`run_backtest`,
      :func:`scale_inputs_for_prices`, :func:`max_drawdown`

**Constraints** — SLSQP constraint builders
    * :func:`fun_of`, :func:`budget`, :func:`bounds`,
      :func:`inequality`, :func:`merge`, :func:`budget_with_extras`,
      :func:`long_only_inequalities`, :func:`long_only_bounds`,
      :func:`position_limits_inequalities`,
      :func:`position_limits_bounds`,
      :func:`sector_caps_inequalities`,
      :func:`leverage_cap_inequality`

**Pipeline** — observability and reproducibility
    * :class:`Logger` — stdlib logging facade
    * :class:`Reproduce` — single-run pipeline execution
    * :class:`Report` — determinism report over repeated runs
"""

from convexfolio.config import (
    Experiment,
    Load,
    Optimization,
    PortfolioInputs,
    Runtime,
    Validate,
)
from convexfolio.data import LoadCSV, Summary, SyntheticPortfolio
from convexfolio.hf_data import (
    DATASET_REPO_ID,
    DATASET_SPLIT,
    DATASET_SUBSET,
    HV_COLUMNS,
    IV_BUCKETS,
    BucketWeightStat,
    BuildPortfolioInputs,
    CrossSectionResult,
    CrossSectionRunner,
    CSVFileSource,
    HFDatasetSource,
    LoadOptionsIV,
    OptionsRow,
    Parse,
    SummariseResults,
)
from convexfolio.math import (
    Bilinear,
    CFVaR2Closed,
    CFVaR2nd,
    CFVaR3Numerical,
    CFVaR3Objective,
    CFVaR3rd,
    Compute,
    Cross,
    Cumulant,
    Curvature,
    Expect,
    Greeks,
    Linear,
    Linearize,
    Loss,
    Minimize,
    OptimalEpsilon,
    PortfolioVariance,
    Quadratic,
    QualityScore,
    Reconstruct,
    Score,
    Variance,
)
from convexfolio.utils import Logger, Report, Reproduce

__all__ = [
    "Bilinear",
    "BuildPortfolioInputs",
    "BucketWeightStat",
    "CFVaR2Closed",
    "CFVaR2nd",
    "CFVaR3Numerical",
    "CFVaR3Objective",
    "CFVaR3rd",
    "CSVFileSource",
    "Compute",
    "Cross",
    "CrossSectionResult",
    "CrossSectionRunner",
    "Cumulant",
    "Curvature",
    "DATASET_REPO_ID",
    "DATASET_SPLIT",
    "DATASET_SUBSET",
    "Experiment",
    "Expect",
    "Greeks",
    "HV_COLUMNS",
    "HFDatasetSource",
    "IV_BUCKETS",
    "Linear",
    "Linearize",
    "LoadCSV",
    "Load",
    "LoadOptionsIV",
    "Logger",
    "Loss",
    "Minimize",
    "OptimalEpsilon",
    "Optimization",
    "OptionsRow",
    "Parse",
    "PortfolioInputs",
    "PortfolioVariance",
    "QualityScore",
    "Quadratic",
    "Reconstruct",
"Report",
    "Reproduce",
    "Runtime",
    "Score",
    "SummariseResults",
    "Summary",
    "SyntheticPortfolio",
    "Validate",
    "Variance",
]
