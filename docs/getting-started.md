# Getting Started

This guide will help you get started with the Optimal Option Portfolios package.

## Prerequisites

- Python 3.10 or higher
- pip package manager

## Installation

### From Source (Recommended)

```bash
git clone https://github.com/sachncs/optimal-option-portfolios.git
cd optimal-option-portfolios
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Verify Installation

```bash
python -c "import options; print(oop.__all__)"
```

## Quick Start

### Python API

```python
import numpy as np
from options import solve_variance_minimization

# Define problem inputs
qmatrix = np.array([[2.0, 0.1], [0.1, 1.5]])
v = np.array([1.2, 0.8])

# Solve
weights = solve_variance_minimization(v=v, qmatrix=qmatrix)
print(f"Optimal weights: {weights}")
print(f"Budget constraint: {weights.T @ v:.6f} (should be 1.0)")
```

### Command Line

```bash
# Generate a reproduction report
options --command reproduce-report

# Print report to stdout
options --command print-report

# Validate deterministic behavior
options --command validate-determinism
```

## Configuration

Create a `config.json` file:

```json
{
  "runtime": {
    "seed": 42,
    "log_level": "DEBUG",
    "output_dir": "results"
  },
  "optimization": {
    "alpha": 0.10,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
```

Use it with:

```bash
options --config config.json --command reproduce-report
```

## Next Steps

- Read the [Architecture Guide](architecture.md) for design details
- See the [API Reference](api-reference.md) for function signatures
- Review [Deployment Guide](deployment.md) for production use
- Check [FAQ](faq.md) for common questions
