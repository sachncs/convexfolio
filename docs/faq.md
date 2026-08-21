# Frequently Asked Questions

## General

### What is Convexfolio?

Convexfolio is a Python package for portfolio optimization based on the paper [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2). It implements variance minimization and risk-aware optimization using conditional fractional Value-at-Risk (CFVaR).

### What Python versions are supported?

Python 3.12 and higher. We recommend using the latest stable version.

### Is this package production-ready?

Yes. The package includes:
- Type annotations for all public APIs
- Deterministic execution with validation
- Structured JSON outputs
- Comprehensive test suite
- CI/CD pipeline

## Installation

### How do I install the package?

```bash
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### What are the dependencies?

Core (exact pins):
- numpy == 2.5.2
- scipy == 1.18.0

Development (exact pins):
- pytest == 9.1.1
- mypy == 2.3.1
- ruff == 0.16.4

Optional:
- pyyaml == 6.0.3 (YAML config support)
- pytest-benchmark == 5.2.3, py-cpuinfo == 9.0.0 (benchmarking)

## Usage

### How do I solve a portfolio optimization problem?

```python
import numpy as np
from convexfolio import Variance, Minimize

precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
cost_vector = np.array([1.2, 0.8])

weights = Minimize(Variance(precision_matrix), cost_vector).value
```

### What is the budget constraint?

The budget constraint ensures that the sum of weighted option prices equals 1:

```
x^T v = 1
```

This is automatically enforced by all solvers.

### How do I ensure deterministic results?

1. Set a fixed seed in your configuration:
   ```json
   {"runtime": {"seed": 42}}
   ```

2. Validate determinism:
   ```bash
   convexfolio --command validate-determinism --repetitions 3
   ```

### What is CFVaR?

CFVaR (Conditional Fractional Value-at-Risk) is a risk measure that captures tail risk beyond traditional VaR. The package implements two variants:
- CFVaR2: Second-order approximation (analytical solution)
- CFVaR3: Third-order approximation (numerical solution)

## Configuration

### Where do I put my configuration file?

Create a `config.json` file and pass it to the CLI:

```bash
convexfolio --config config.json --command reproduce-report
```

### What is the alpha parameter?

Alpha (α) is the risk parameter controlling the confidence level for CFVaR calculations. It must satisfy 0 < α < 0.5. Default is 0.05.

### Can I use YAML configuration?

Yes — files with a `.yaml` or `.yml` suffix are parsed by PyYAML. JSON (`.json`) is also supported. Install the `yaml` extra: `pip install '.[yaml]'`.

## Development

### How do I run tests?

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

### How do I run the linter?

```bash
ruff check convexfolio tests scripts benchmarks
```

### How do I run the type checker?

```bash
mypy convexfolio
```

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Troubleshooting

### I get "Module not found" errors

Ensure your virtual environment is activated:
```bash
source .venv/bin/activate
```

### The optimization is slow

- Check matrix conditioning
- Reduce portfolio size if possible
- Ensure numpy/scipy are installed with optimized BLAS

### Results are not deterministic

- Verify the seed is fixed in configuration
- Check that no external random state is being used
- Run `validate-determinism` to verify

### I get numerical errors

- Check for singular matrices
- Ensure inputs are well-conditioned
- Review the alpha parameter value

## Support

- **Issues**: [GitHub Issues](https://github.com/sachncs/convexfolio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sachncs/convexfolio/discussions)
- **Security**: See [SECURITY.md](../SECURITY.md)
