"""Public package API for the Convexfolio package.

The API is grouped by responsibility:

* **Configuration** — :class:`Experiment`, :class:`Runtime`,
  :class:`Optimization`, :class:`PortfolioInputs`,
  :class:`Load`, :class:`Validate`.
* **Data ingestion** — :class:`LoadCSV`,
  :class:`SyntheticPortfolio`, :class:`Summary`.
* **SP500 options-IV HuggingFace integration** —
  :class:`OptionsRow`, :class:`CrossSectionResult`,
  :class:`BucketWeightStat`, :class:`HFDatasetSource`,
  :class:`CSVFileSource`, :class:`LoadOptionsIV`,
  :class:`BuildPortfolioInputs`, :class:`SummariseResults`,
  :class:`CrossSectionRunner`, :class:`Parse`, plus the
  :data:`IV_BUCKETS`, :data:`HV_COLUMNS`, and ``DATASET_*`` constants.
* **Math** — the closed-form portfolio primitives
  (:class:`Variance`, :class:`Minimize`, :class:`CFVaR2Closed`,
  :class:`CFVaR3Numerical`, and friends) plus the skew-t building
  blocks (:class:`Compute`, :class:`Linear`, :class:`Curvature`,
  :class:`Bilinear`, :class:`Cross`).
* **Pipeline** — :class:`Logger`, :class:`Report`,
  :class:`Reproduce`.
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
