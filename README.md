<p align="center">
  <h1 align="center">Optimal Option Portfolios</h1>
  <p align="center">Production-ready option portfolio optimization with variance minimization and CFVaR2 closed-form solutions.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/optimal-option-portfolios/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/optimal-option-portfolios/ci.yml?branch=main" alt="CI"></a>
    <a href="https://github.com/sachncs/optimal-option-portfolios/stargazers"><img src="https://img.shields.io/github/stars/sachncs/optimal-option-portfolios" alt="Stars"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Ruff"></a>
    <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type%20checked-mypy-blue.svg" alt="mypy"></a>
  </p>
</p>

Production-ready Python package for optimal option portfolio optimization,
based on [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2).

---

## Features

- **Variance Minimization** — Solve minimum-variance portfolio allocation under budget constraints
- **CFVaR2 Closed-Form** — Analytical solution for conditional fractional Value-at-Risk (2nd order)
- **CFVaR3 Numerical** — Numerical optimization for higher-order risk measures
- **Deterministic Execution** — Seed-controlled reproducibility for auditing and validation
- **Production CLI** — Command-line interface for reproducible report generation
- **Typed API** — Full type annotations for integration into external systems
- **Structured Outputs** — JSON reports for downstream orchestration and analysis

---

## Installation

### From source

```bash
git clone https://github.com/sachncs/optimal-option-portfolios.git
cd optimal-option-portfolios
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

---

## Quick Start

### CLI

```bash
# Generate reproduction report
options --command reproduce-report

# Print report to stdout
options --command print-report

# Validate deterministic behavior
options --command validate-determinism --repetitions 3

# Use custom config
options --config config.json --command reproduce-report
```

### Python API

```python
import numpy as np
from options import solve_variance_minimization, solve_cfvar2_closed_form

# Define inputs
q_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
v = np.array([1.2, 0.8])
u = np.array([0.1, 0.3])

# Solve variance minimization
weights = solve_variance_minimization(v=v, q_matrix=q_matrix)
print(f"Variance solution: {weights}")

# Solve CFVaR2
cfvar2_weights = solve_cfvar2_closed_form(q_matrix=q_matrix, u=u, v=v, alpha=0.05)
print(f"CFVaR2 solution: {cfvar2_weights}")
```

### Demo Script

```bash
python scripts/demo.py
```

---

## Configuration

Create a `config.json` to customize execution:

```json
{
  "runtime": {
    "seed": 7,
    "log_level": "INFO",
    "output_dir": "artifacts"
  },
  "optimization": {
    "alpha": 0.05,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
```

| Parameter | Env Variable | Default | Description |
|-----------|--------------|---------|-------------|
| `runtime.seed` | — | `7` | Random seed for deterministic execution |
| `runtime.log_level` | — | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `runtime.output_dir` | — | `artifacts` | Directory for output reports |
| `optimization.alpha` | — | `0.05` | Risk parameter (must be between 0 and 0.5) |
| `optimization.method` | — | `all` | Optimization method to run |
| `optimization.enforce_nu_greater_than_six` | — | `true` | Enforce nu > 6 constraint |

---

## API

| Symbol | Type | Description |
|--------|------|-------------|
| `solve_variance_minimization` | function | Closed-form QP for the minimum-variance portfolio |
| `compute_epsilon_star` | function | Bisection root of the constrained 1-D variance/CFVaR2 equation |
| `solve_cfvar2_closed_form` | function | Closed-form QP for 2nd-order CFVaR |
| `solve_cfvar3_numerical` | function | Iterative solver for 3rd-order (and higher) CFVaR |
| `build_cfvar3_objective` | function | Closure factory for the cfvar3 objective (use `solve_cfvar3_numerical`) |
| `validate_shapes` | function | Validates shape compatibility across risk / optimization inputs |
| `cfvar2`, `cfvar3`, `kappa3` | functions | Risk primitives: 2nd/3rd-order CFVaR and 3rd standardized cumulant |
| `Experiment` | dataclass | Runtime + optimization configuration object (flattened in 0.3.0) |
| `load`, `validate` | functions | JSON config loader and validator |
| `main` | function | CLI entry point (`oop`) |

---

## Examples

```bash
# 1. Run the canonical reproduction and write artifacts to the default dir.
options --command reproduce-report

# 2. Print the same report to stdout for inspection.
options --command print-report

# 3. Confirm three consecutive runs produce identical output.
options --command validate-determinism --repetitions 3

# 4. Re-run the reproduction with a different alpha and output dir.
options --config config.json --command reproduce-report
```

A runnable end-to-end demo is provided:

```bash
python scripts/demo.py
```

---

## Project Structure

```
optimal-option-portfolios/
├── options/              # Main package source
│   ├── __init__.py       # Public API exports
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── determinism.py    # Deterministic validation
│   ├── logging_utils.py  # Logging utilities
│   ├── moments.py        # Moment calculations
│   ├── optimization.py   # Core optimization solvers
│   ├── pipeline.py       # Execution pipeline
│   ├── pricing.py        # Pricing functions
│   ├── reproduction_math.py  # Reproduction math
│   ├── risk.py           # Risk measures (CFVaR)
│   └── types.py          # Type definitions
├── tests/                # Test suite
├── scripts/              # Demo and utility scripts
├── docs/                 # Documentation
├── artifacts/            # Generated outputs
└── .github/              # GitHub configuration
```

---

## Development

```bash
# Install dependencies
pip install -e .[dev]

# Run linter
ruff check src tests scripts

# Run type checker
mypy options

# Run tests
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

# Build package
python -m build

# Run demo
python scripts/demo.py
```

### Quality Gates

```bash
# Full quality check
ruff check src tests scripts && mypy options && PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q && python -m build
```

---

## Testing

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=options
```

---

## Build

```bash
python -m build
```

---

## Release

Version is bumped in `pyproject.toml`, the changelog is updated in
`CHANGELOG.md`, a `vX.Y.Z` tag is cut, and the PyPI publishing workflow
publishes the source and wheel distributions. See
[docs/release.md](docs/release.md) for the full process.

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python >= 3.10 |
| Numerical | [NumPy](https://numpy.org/) >= 1.26, [SciPy](https://scipy.org/) >= 1.11 |
| Testing | [pytest](https://docs.pytest.org/) >= 8.0 |
| Type Check | [mypy](https://mypy-lang.org/) >= 1.10 |
| Lint/Format | [Ruff](https://docs.astral.sh/ruff/) >= 0.6 |
| Build | [Setuptools](https://setuptools.pypa.io/) >= 68 |

---

## Roadmap

- [ ] Add real-market data ingestion support
- [ ] Implement additional risk measures
- [ ] Add YAML configuration support
- [ ] Create API documentation with autodoc
- [ ] Add performance benchmarks
- [ ] Implement parallel processing for large portfolios
- [ ] Add visualization utilities
- [ ] Create Docker support

---

## Fidelity and Mismatches

- [Fidelity report](docs/fidelity_report.md)
- [Mismatch report](docs/mismatch_report.md)
- [Determination notes](docs/research_determination.md)
- [Release process](docs/release.md)

Missing details are explicitly marked where relevant:

- `NOT DETERMINED`
- `ASSUMPTION`
- `UNKNOWN`

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for our community standards.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
