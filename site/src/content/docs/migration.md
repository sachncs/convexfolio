---
title: "Migration to the validated API"
---
# Migration to the validated API

The current development line introduces a validated, diagnostic API around
the existing numerical primitives. Treat it as a breaking v2 migration when
moving an application from the earlier interface.

## Array ownership and validation

Replace module-level copy/validation helpers with the value-object methods:

```python
from convexfolio import Matrix, Vector

costs = Vector([0.6, 0.4])
precision = Matrix([[2.0, 0.1], [0.1, 1.5]])

costs.validate("cost_vector", positive=True)
precision.validate("precision_matrix")
writable_costs = costs.copy()
```

`Vector` and `Matrix` own a copied, read-only boundary representation. Use
`.copy()` when a writable working array is required; do not mutate arrays
stored inside a configuration or result object.

## Solver and risk contracts

New code should compose the public contracts rather than dispatch on class
names:

```python
from convexfolio import (
    BudgetConstraint,
    ClosedFormVarianceOptimizer,
    OptimizationProblem,
    VarianceRisk,
)

problem = OptimizationProblem(
    inputs=portfolio_inputs,
    constraints=(BudgetConstraint(portfolio_inputs.cost_vector),),
)
result = ClosedFormVarianceOptimizer().solve(
    problem, VarianceRisk(portfolio_inputs)
)
assert result.feasible
```

`OptimizationResult.diagnostics` contains constraint checks and solver
metadata. Handle `ValidationError`, `InfeasibleProblemError`, and
`SolverFailureError` explicitly at application boundaries.

## Configuration and optional features

- Python support is 3.12–3.14.
- Core installation includes NumPy, SciPy, and PyYAML.
- Install plotting with `pip install 'convexfolio[plot]'`.
- Install Hugging Face ingestion with `pip install 'convexfolio[hf-data]'`.
- Install development tooling with `pip install -e '.[dev,plot,hf-data]'`.
- Unknown configuration keys now fail validation instead of being ignored.

## Backtesting changes

Backtests now track holdings, mark the portfolio to market between
rebalances, apply transaction costs to turnover, and expose cumulative costs
and drawdown in the result summary. A tolerated solver failure is opt-in and
is rejected if its fallback violates the budget or configured constraints.
