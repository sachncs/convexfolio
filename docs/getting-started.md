# Getting Started

This guide will help you get started with the Convexfolio package.

## Prerequisites

- Python 3.12 or higher
- pip package manager

## Installation

### From Source (Recommended)

```bash
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### Verify Installation

```bash
python -c "import convexfolio; print(convexfolio.__all__)"
```

## Quick Start

### Python API

```python
import numpy as np
from convexfolio import Variance, Minimize

# Define problem inputs
precision_matrix = np.array([[2.0, 0.1], [0.1, 1.5]])
cost_vector = np.array([1.2, 0.8])

# Solve
weights = Minimize(Variance(precision_matrix), cost_vector).value
print(f"Optimal weights: {weights}")
print(f"Budget constraint: {weights.T @ cost_vector:.6f} (should be 1.0)")
```

### Command Line

```bash
# Generate a reproduction report
convexfolio --command reproduce-report

# Print report to stdout
convexfolio --command print-report

# Validate deterministic behavior
convexfolio --command validate-determinism
```

## Configuration

Create a `config.json` file:

```json
{
  "runtime": {
    "seed": 42,
    "log_level": "DEBUG",
    "output_directory": "results"
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
convexfolio --config config.json --command reproduce-report
```

## Next Steps

- Read the [Architecture Guide](architecture.md) for design details
- See the [API Reference](api-reference.md) for function signatures
- Review [Deployment Guide](deployment.md) for production use
- Check [FAQ](faq.md) for common questions
