# Contributing to Convexfolio

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Running Tests](#running-tests)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/convexfolio.git
   cd convexfolio
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/sachncs/convexfolio.git
   ```
4. **Create a feature branch** from `main`

## Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -e '.[dev]'
   ```

3. **Verify setup**:
   ```bash
   ruff check convexfolio tests scripts benchmarks
   mypy convexfolio
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
   ```

## Branch Naming

Use descriptive branch names with prefixes:

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code refactoring |
| `test/` | Adding or updating tests |
| `chore/` | Maintenance tasks |

Examples:
- `feat/add-parallel-processing`
- `fix/cfvar3-convergence-issue`
- `docs/update-api-reference`

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |
| `ci` | CI/CD changes |

### Examples

```bash
feat(optimization): add parallel solver for large portfolios
fix(risk): correct CFVaR3 edge case calculation
docs(api): update function signatures
test(pipeline): add integration tests
chore(deps): update scipy to 1.12
```

## Pull Request Process

1. **Update your fork** with latest upstream changes:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Make your changes** following coding standards

4. **Run quality checks**:
   ```bash
   ruff check convexfolio tests scripts benchmarks
   mypy convexfolio
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
   ```

5. **Commit with conventional message**:
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feat/your-feature-name
   ```

7. **Fill out PR template** completely

### PR Requirements

- [ ] All CI checks pass
- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)
- [ ] Branch is up-to-date with `main`

## Coding Standards

### Python Style

- Follow PEP 8 with line length of 88 (Ruff default).
- Use type annotations for all public functions.
- Write Google-style docstrings for every public module, class, and function.
- `snake_case` for functions/variables; `CapWords` for classes; lowercase single words for module names.
- **No leading-underscore "private" names on top-level identifiers.** Public surface is declared via `__all__` in each module's top-level. Helper functions that are part of the public API keep public names. Reserved dunders (`__init__`, `__all__`, `__post_init__`, `__pycache__`, `__main__`) follow Python's own conventions. No name mangling (`__name__`) outside of Python-mandated slots.
- **No math shorthand as identifier names.** `g1`, `g2`, `q`, `eps_star`, `nu`, `sigma`, `omega`, `theta`, `m`, `x`, `z`, `psi`, `tau`, `kappa3` (alone) are forbidden as variable names. Use full descriptive words (`loss_gradient`, `constraint_gradient`, `precision_matrix`, `optimal_epsilon`, `degrees_of_freedom`, `covariance`, `skewness`, `price_drift`, `instrument_count`, `weights`, `z_score`, `dual_variable`, `tau`, `third_order_cumulant`).
- **No `try/except` without a typed reason.** Catch only specific named exceptions (`ValueError`, `FileNotFoundError`, `json.JSONDecodeError`, `KeyError`, `TypeError`, etc.). Never `except Exception:` or bare `except:`. Let unexpected exceptions propagate.
- **No new abstraction.** No `Builder`/`Manager`/`Factory`/`Strategy`/`Handler`/`Service`/`Helper`/`Util` suffixes. No `ABC`, no `Protocol`, no `isinstance` dispatch. Inline closure bodies where they fit; the rest are hoisted as module-level functions.

### Ruff Configuration

The project uses Ruff for linting with default settings:

```toml
[tool.ruff]
line-length = 88
```

### Mypy Configuration

```toml
[tool.mypy]
python_version = "3.12"
strict = false
warn_unused_ignores = true
warn_return_any = false
```

### Import Order

```python
# Standard library
import json
from pathlib import Path

# Third-party
import numpy as np
from scipy import optimize

# Local
from convexfolio.config import Experiment
from convexfolio.math import CFVaR2Closed
```

## Running Tests

### Full Test Suite

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

### Specific Test File

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_optimization.py
```

### With Coverage

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest --cov=convexfolio --cov-report=html
```

## Documentation

### Writing Docstrings

Use Google-style docstrings:

```python
class Variance:
    """Callable portfolio variance objective.

    Args:
        precision_matrix: 2-D precision matrix ``Q``.
    """

    def __call__(self, weights: FloatArray) -> float:
        """Return ``0.5 x^T Q x`` at the given weights."""
```

### Updating Documentation

- Keep README.md up-to-date with API changes
- Update CHANGELOG.md following Keep a Changelog format
- Add examples for new features
- Update docstrings for modified functions

## Questions?

Feel free to open an issue for questions or discussions!
