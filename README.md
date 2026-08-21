<p align="center">
  <h1 align="center">Convexfolio</h1>
  <p align="center">Production-ready option portfolio optimization with variance minimization and CFVaR2 closed-form solutions.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/convexfolio/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/convexfolio/ci.yml?branch=main" alt="CI"></a>
    <a href="https://github.com/sachncs/convexfolio/stargazers"><img src="https://img.shields.io/github/stars/sachncs/convexfolio" alt="Stars"></a>
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
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

---

## Quick Start

### CLI

```bash
# Generate reproduction report
convexfolio --command reproduce-report

# Print report to stdout
convexfolio --command print-report

# Validate deterministic behavior
convexfolio --command validate-determinism --repetitions 3

# Use custom config
convexfolio --config config.json --command reproduce-report
```

### Python API

```python
import numpy as np
from convexfolio import Variance, Minimize, CFVaR2Closed, CFVaR2nd

# Define inputs
precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
cost_vector = np.array([1.2, 0.8])
expected_payoff = np.array([0.1, 0.3])

# Solve variance minimization (closed-form)
weights = Minimize(Variance(precision_matrix), cost_vector).value
print(f"Variance solution: {weights}")

# Solve CFVaR2 (closed-form)
cfvar2_weights = CFVaR2Closed(
    precision_matrix=precision_matrix,
    expected_payoff=expected_payoff,
    cost_vector=cost_vector,
    alpha=0.05,
).value

# Evaluate CFVaR2 risk number at any weight vector
risk = CFVaR2nd(
    alpha=0.05,
    expected_payoff=expected_payoff,
    precision_matrix=precision_matrix,
    weights=weights,
).value
print(f"CFVaR2 risk at variance weights: {risk}")
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
    "output_directory": "artifacts"
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
| `runtime.output_directory` | — | `artifacts` | Directory for output reports |
| `optimization.alpha` | — | `0.05` | Risk parameter (must be between 0 and 0.5) |
| `optimization.method` | — | `all` | Optimization method to run |
| `optimization.enforce_nu_greater_than_six` | — | `true` | Enforce nu > 6 constraint |

---

## API

The full API surface is documented in [docs/api-reference.md](docs/api-reference.md). Highlights:

| Symbol | Type | Description |
|--------|------|-------------|
| `Variance`, `Minimize` | classes | Closed-form variance minimization under budget |
| `CFVaR2Closed` | class | Closed-form CFVaR2 weight solver |
| `CFVaR3Numerical`, `CFVaR3Objective` | classes | Numerical CFVaR3 solver + objective factory |
| `CFVaR2nd`, `CFVaR3rd` | classes | 2nd / 3rd-order CFVaR risk evaluators |
| `Experiment`, `Runtime`, `Optimization` | dataclasses | Configuration object graph |
| `load`, `validate` | functions | JSON/YAML config loader and validator |
| `check` | function | Determinism validation across repeated runs |
| `reproduce`, `run_and_save` | functions | Pipeline execution and persistence |

---

## Examples

```bash
# 1. Run the canonical reproduction and write artifacts to the default dir.
convexfolio --command reproduce-report

# 2. Print the same report to stdout for inspection.
convexfolio --command print-report

# 3. Confirm three consecutive runs produce identical output.
convexfolio --command validate-determinism --repetitions 3

# 4. Re-run the reproduction with a different alpha and output dir.
convexfolio --config config.json --command reproduce-report
```

A runnable end-to-end demo is provided:

```bash
python scripts/demo.py
```

---

## Project Structure

```
convexfolio/
├── convexfolio/         # Main package source
│   ├── __init__.py      # Public API exports
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Configuration dataclasses + loader
│   ├── determinism.py   # Determinism validation
│   ├── math.py          # Risk, optimisation, section-2.4 primitives
│   ├── pipeline.py      # Run + persist report
│   ├── types.py         # Type definitions
│   └── utils.py         # Logger, Report, reproduce()
├── tests/               # Test suite
├── benchmarks/          # pytest-benchmark suite
├── scripts/             # Demo and utility scripts
├── docs/                # Markdown documentation
└── .github/             # GitHub configuration
```

---

## Development

```bash
# Install dependencies
pip install -e '.[dev]'

# Run linter
ruff check convexfolio tests scripts benchmarks

# Run type checker
mypy convexfolio

# Run tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

# Build package
python -m build

# Run demo
python scripts/demo.py
```

### Quality Gates

```bash
ruff check convexfolio tests scripts benchmarks && mypy convexfolio && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q && python -m build
```

---

## Testing

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=convexfolio
```

---

## Build

```bash
python -m build
```

---

## Release

Version is bumped in `pyproject.toml`, the changelog is updated in
`CHANGELOG.md`, and a `vX.Y.Z` tag is cut. See
[docs/release.md](docs/release.md) for the full process.

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python >= 3.12 |
| Numerical | [NumPy](https://numpy.org/) == 2.5.2, [SciPy](https://scipy.org/) == 1.18.0 |
| Testing | [pytest](https://docs.pytest.org/) == 9.1.1, [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) == 5.2.3 |
| Type Check | [mypy](https://mypy-lang.org/) == 2.3.1 |
| Lint/Format | [Ruff](https://docs.astral.sh/ruff/) == 0.16.4 |
| Build | [Setuptools](https://setuptools.pypa.io/) == 84.0.0 |

All dependencies are pinned to exact versions.

---

## Roadmap

- [ ] Add real-market data ingestion support
- [ ] Implement additional risk measures
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
