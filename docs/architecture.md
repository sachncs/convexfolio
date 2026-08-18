# Architecture

## Overview

The Optimal Option Portfolios package implements portfolio optimization algorithms based on the paper [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2). It provides both a Python API and CLI for solving variance minimization and risk-aware portfolio allocation problems.

## Package Structure

```
options/
├── __init__.py          # Public API exports
├── cli.py               # Command-line interface
├── config.py            # Configuration management
├── determinism.py       # Deterministic validation
├── logging_utils.py     # Logging utilities
├── moments.py           # Moment calculations
├── optimization.py      # Core solvers
├── pipeline.py          # Execution pipeline
├── pricing.py           # Pricing functions
├── reproduction_math.py # Reproduction math
├── risk.py              # Risk measures (CFVaR)
└── types.py             # Type definitions
```

## Core Components

### Types (`types.py`)

Defines typed data containers:

- `PortfolioState` — State variables in Setting 2.1
- `DistributionParameters` — Distributional objects from Section 2 and 4
- `IntermediateMoments` — Intermediate vectors/matrices from Eq. (3)

### Optimization (`optimization.py`)

Core solvers:

- `solve_variance_minimization` — Minimum variance portfolio under budget constraint
- `solve_cfvar2_closed_form` — Analytical CFVaR2 solution
- `solve_cfvar3_numerical` — Numerical CFVaR3 optimization
- `build_cfvar3_objective` — Build CFVaR3 objective function

### Risk (`risk.py`)

Risk measures:

- `cfvar2` — Conditional fractional Value-at-Risk (2nd order)
- `cfvar3` — Conditional fractional Value-at-Risk (3rd order)

### Configuration (`config.py`)

- `RuntimeConfig` — Execution settings (seed, log level, output dir)
- `OptimizationConfig` — Optimization parameters (alpha, method)
- `ExperimentConfig` — Top-level configuration container

### Pipeline (`pipeline.py`)

- `run_reproduction` — Execute end-to-end optimization
- `save_report` — Persist JSON reports

### CLI (`cli.py`)

Commands:
- `reproduce-report` — Generate and save report
- `print-report` — Print report to stdout
- `validate-determinism` — Verify reproducibility

## Data Flow

```
Config → Pipeline → Solvers → Risk Measures → Report
  ↓          ↓           ↓            ↓           ↓
JSON    Synthetic    Optimize    Calculate    JSON
File    Data Gen     Weights     CFVaR        Output
```

## Deterministic Execution

The package ensures reproducibility through:

1. Seed-controlled random number generation
2. Frozen configuration dataclasses
3. Deterministic validation via `validate-determinism`

## Design Principles

1. **Paper Faithful** — Implements the paper's algorithms accurately
2. **Production Ready** — Typed API, structured outputs, error handling
3. **Extensible** — Plugin-friendly for custom data ingestion
4. **Auditable** — Deterministic execution with validation
