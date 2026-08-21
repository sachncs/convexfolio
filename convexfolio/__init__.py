"""Public package API for the Convexfolio package.

The API is grouped by responsibility:

* **Configuration** — :class:`Experiment`, :class:`Runtime`,
  :class:`Optimization`, :class:`PortfolioInputs`, :func:`load`,
  :func:`validate`.
* **Data ingestion** — :func:`load_csv`, :func:`synthetic_portfolio`,
  :func:`to_config`, :func:`summary`.
* **SP500 options-IV HuggingFace integration** —
  :class:`OptionsRow`, :class:`CrossSectionResult`,
  :class:`BucketWeightStat`, :class:`HFDatasetSource`,
  :class:`CSVFileSource`, :class:`LoadOptionsIV`,
  :class:`BuildPortfolioInputs`, :class:`SummariseResults`,
  :class:`CrossSectionRunner`, :func:`parse_options_row`, plus the
  :data:`IV_BUCKETS`, :data:`HV_COLUMNS`, and ``DATASET_*`` constants.
* **Math** — the closed-form portfolio primitives
  (:class:`Variance`, :class:`Minimize`, :class:`CFVaR2Closed`,
  :class:`CFVaR3Numerical`, and friends) plus the skew-t building
  blocks (:class:`Compute`, :class:`Linear`, :class:`Curvature`,
  :class:`Bilinear`, :class:`Cross`).
* **Pipeline** — :class:`Logger`, :class:`Report`,
  :func:`reproduce`, :func:`check` (determinism check).
"""

from convexfolio.config import (
    Experiment,
    Optimization,
    PortfolioInputs,
    Runtime,
    load,
    validate,
)
from convexfolio.data import load_csv, summary, synthetic_portfolio, to_config
from convexfolio.determinism import check
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
    SummariseResults,
    parse_options_row,
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
from convexfolio.utils import Logger, Report, reproduce

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
    "LoadOptionsIV",
    "Logger",
    "Loss",
    "Minimize",
    "OptimalEpsilon",
    "Optimization",
    "OptionsRow",
    "PortfolioInputs",
    "PortfolioVariance",
    "QualityScore",
    "Quadratic",
    "Reconstruct",
    "Report",
    "Runtime",
    "Score",
    "SummariseResults",
    "Variance",
    "check",
    "load",
    "load_csv",
    "parse_options_row",
    "reproduce",
    "summary",
    "synthetic_portfolio",
    "to_config",
    "validate",
]
