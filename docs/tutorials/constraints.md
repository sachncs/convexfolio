# Tutorial: Constrained Portfolio Optimisation

This tutorial shows you how to add real-world constraints to a
portfolio — long-only, position limits, sector caps, leverage cap.

> 📖 **New here?** See the [Glossary](../glossary.md).

**Time required**: ~10 minutes.

---

## What you'll build

By the end, you'll have a portfolio with:

1. **Long-only** — no shorting.
2. **Position limits** — no single option gets more than 25% of the
   portfolio.
3. **Sector caps** — no sector gets more than 50% of the portfolio.

And you'll see how each constraint changes the recommended split.

---

## The story

> You manage $10M across five option contracts. You're a
> long-only fund (the prospectus forbids shorting). Your compliance
> team has rules:
>
> - No single position can be more than 25% of the portfolio.
> - No sector can be more than 50% of the portfolio.
>
> How does this change the recommended weights?

---

## Step 1 — Load inputs

```python
import numpy as np
from convexfolio.data import load_csv

inputs = load_csv("portfolio.csv")
print(f"Loaded {inputs.n_instruments} options")
```

If you don't have a `portfolio.csv` yet, see the
[from-CSV tutorial](from-csv.md).

---

## Step 2 — Build the constraints

```python
from convexfolio.constraints import (
    long_only_inequalities,
    position_limits_inequalities,
    sector_caps_inequalities,
)
```

Each helper returns a tuple of SLSQP constraints.

```python
n = inputs.n_instruments
sector_map = [0, 0, 1, 1, 2]  # five options across three sectors

constraints = (
    long_only_inequalities(n)
    + position_limits_inequalities(n, max_abs_weight=0.25)
    + sector_caps_inequalities(sector_map, max_per_sector=0.50)
)
```

Let's break that down:

- `long_only_inequalities(n)` — returns ``n`` inequalities, one per
  instrument, enforcing ``x[i] >= 0``.
- `position_limits_inequalities(n, max_abs_weight=0.25)` — returns
  ``2n`` inequalities enforcing ``|x[i]| <= 0.25``.
- `sector_caps_inequalities(sector_map, max_per_sector=0.50)` —
  returns one inequality per unique sector enforcing
  ``sum_{i in sector} x[i] <= 0.50``.

Tuples concatenate with `+` so you can layer constraints.

---

## Step 3 — Solve

```python
from convexfolio import CFVaR3Numerical, CFVaR3Objective

objective = CFVaR3Objective(
    alpha=0.05,
    expected_payoff=inputs.expected_payoff,
    precision_matrix=inputs.precision_matrix,
    kappa3_callback=lambda w: 0.0,
)

weights = CFVaR3Numerical(
    cost_vector=inputs.cost_vector,
    initial_weights=inputs.cost_vector / float(inputs.cost_vector @ inputs.cost_vector),
    objective_callable=objective,
    extra_constraints=constraints,
).value
```

The `extra_constraints` argument is the new piece — pass your
constraint tuple here. The budget constraint is added automatically.

---

## Step 4 — Check the result

```python
print(f"Weights: {weights}")
print(f"All non-negative? {bool(np.all(weights >= -1e-8))}")
print(f"All <= 25%? {bool(np.all(np.abs(weights) <= 0.25 + 1e-8))}")
print(f"Budget holds? {np.isclose(float(weights @ inputs.cost_vector), 1.0)}")
for sector in sorted(set(sector_map)):
    indices = [i for i, s in enumerate(sector_map) if s == sector]
    sector_sum = float(sum(weights[i] for i in indices))
    print(f"  Sector {sector}: {sector_sum:.3f} (cap 0.50)")
```

You should see all four `True` / within-cap outputs.

---

## Step 5 — Try without constraints

Run the same solver **without** the `extra_constraints` argument and
compare:

```python
weights_unconstrained = CFVaR3Numerical(
    cost_vector=inputs.cost_vector,
    initial_weights=inputs.cost_vector / float(inputs.cost_vector @ inputs.cost_vector),
    objective_callable=objective,
).value
print(f"Unconstrained weights: {weights_unconstrained}")
```

You'll likely see negative weights (short positions) and larger
magnitudes. That's the "pure math" answer; the constrained answer is
what a real fund could actually implement.

---

## What can go wrong

| Error | Cause | Fix |
|---|---|---|
| `Optimisation failed` | Constraints are infeasible together. | Loosen one (e.g., bigger sector cap). |
| `weights` all near zero | The cost vector doesn't allow a feasible solution under your caps. | Reduce position limit or sector cap. |
| `RuntimeError: SLSQP` | Numerical issue on edge cases. | Try a different starting point. |

---

## All constraint helpers at a glance

| Helper | Returns | Effect |
|---|---|---|
| `long_only_inequalities(n)` | `n` inequalities | `x[i] >= 0` |
| `long_only_bounds(n)` | `n` bounds | `(0, inf)` |
| `position_limits_inequalities(n, max_abs)` | `2n` inequalities | `|x[i]| <= max_abs` |
| `position_limits_bounds(n, max_abs)` | `n` bounds | `(-max_abs, +max_abs)` |
| `sector_caps_inequalities(sector_map, max_per_sector)` | one inequality per unique sector | sector sum `<= max_per_sector` |
| `leverage_cap_inequality(n, max_leverage)` | one inequality | `sum |x[i]| <= max_leverage` |
| `budget(cost_vector)` | one equality | `x . v == 1` |
| `inequality(a, limit)` | one inequality | `a . x <= limit` |
| `merge(*groups)` | flat tuple | concatenate constraint groups |
| `budget_with_extras(v, *extras)` | budget + extras | convenience |

---

## Where to look next

- **[API Reference](../api-reference.md)** — Full constraint API.
- **[Glossary](../glossary.md)** — Plain-English definitions.
- **[from-CSV tutorial](from-csv.md)** — Loading portfolio inputs.
- **[Visualisation tutorial](visualisation.md)** — Plotting the
  results.
