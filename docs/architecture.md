# Architecture

## Overview

The Convexfolio package implements portfolio optimization algorithms based on the paper [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2). It provides both a Python API and CLI for solving variance minimization and risk-aware portfolio allocation problems.

## Package Structure

```
convexfolio/
├── __init__.py          # Public API exports
├── cli.py               # Command-line interface
├── config.py            # Configuration dataclasses + loader
├── determinism.py       # Determinism validation
├── math.py              # Risk, optimisation, section-2.4 primitives
├── pipeline.py          # Run + persist report
├── types.py             # Type aliases (FloatArray)
└── utils.py             # Logger, Report, reproduce()
```

## Core Components

### Types (`types.py`)

Defines typed aliases:

- `FloatArray` — `numpy.typing.NDArray[np.float64]`

### Math primitives (`math.py`)

Core numerical classes, instantiated with deterministic inputs:

- `Compute`, `Linear`, `Curvature` — Skew-t coefficients `c`, `h`, `q`.
- `Bilinear`, `Cross` — Section-2.4 expansion matrices.
- `Expect`, `Quadratic`, `Variance` — Linear and quadratic forms.
- `Cumulant` — Third central moment.
- `Minimize` — Closed-form variance minimisation.
- `Loss`, `Score`, `OptimalEpsilon` — Epsilon-star helpers.
- `CFVaR2Closed` — Closed-form CFVaR2 weight solver.
- `CFVaR3Numerical`, `CFVaR3Objective` — Numerical CFVaR3 solver.
- `CFVaR2nd`, `CFVaR3rd` — Risk evaluators at a weight vector.
- `Greeks`, `PortfolioVariance`, `Linearize`, `Reconstruct` — Section 2.4.
- `QualityScore` — Sanity check on CFVaR2 closed-form.

### Configuration (`config.py`)

- `Runtime` — Execution settings (seed, log level, output directory)
- `Optimization` — Optimization parameters (alpha, method, enforce nu > 6)
- `Experiment` — Top-level configuration container
- `load(path)` — JSON/YAML loader
- `validate(config)` — Semantic constraint enforcement

### Pipeline (`pipeline.py`)

- `run_and_save(experiment, output_dir)` — Execute determinism check and persist report

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
