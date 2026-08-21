# Tutorial: Visualising a Portfolio

This tutorial shows you how to turn Convexfolio's numerical output into
charts you can drop into a slide deck or share with a stakeholder.

> 📖 **New here?** See the [Glossary](../glossary.md).

**Time required**: ~5 minutes.

---

## What you'll build

Three PNGs:

1. `weights.png` — horizontal bar chart of recommended portfolio weights.
2. `frontier.png` — efficient frontier (risk vs return).
3. `cfvar_alpha.png` — risk sensitivity to alpha.

---

## The story

> You've solved a portfolio. The numbers in your terminal say
> `weights = [0.6, 0.9, 0.7, 0.4, 1.0]`. That means nothing to your
> boss.
>
> You need a chart.

---

## Step 1 — Make sure matplotlib is installed

The plot module uses matplotlib. It's an optional dependency (kept
out of the core wheel to keep installs small).

```bash
pip install 'matplotlib==3.11.1'
```

Or with the project's optional extra:

```bash
pip install '.[viz]'
```

(We're adding this extra in a follow-up step. For now, install
matplotlib directly.)

---

## Step 2 — From the CLI

Save your config (with the `inputs` section) to `config.json`:

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
  },
  "inputs": {
    "expected_payoff": [0.05, 0.10, -0.02, 0.08, 0.03],
    "cost_vector": [0.60, 0.40, 0.30, 0.80, 0.50],
    "precision_matrix": [
      [2.0, 0.2, 0.2, 0.2, 0.2],
      [0.2, 1.5, 0.15, 0.15, 0.15],
      [0.2, 0.15, 1.2, 0.12, 0.12],
      [0.2, 0.15, 0.12, 2.5, 0.25],
      [0.2, 0.15, 0.12, 0.25, 1.8]
    ]
  }
}
```

Then:

```bash
convexfolio --config config.json --command plot
```

You'll see three PNGs in `artifacts/`:

```
artifacts/weights.png
artifacts/frontier.png
artifacts/cfvar_alpha.png
```

---

## Step 3 — Just one chart at a time

Use `--chart` to pick a single chart:

```bash
convexfolio --config config.json --command plot --chart weights
convexfolio --config config.json --command plot --chart frontier
convexfolio --config config.json --command plot --chart sensitivity
```

`--chart all` is the default.

---

## Step 4 — From Python

If you want more control, call the plot functions directly:

```python
import numpy as np
from convexfolio import Minimize, Variance
from convexfolio.plot import weights, efficient_frontier, cfvar_sensitivity

precision_matrix = np.array([
    [2.0, 0.2, 0.2, 0.2, 0.2],
    [0.2, 1.5, 0.15, 0.15, 0.15],
    [0.2, 0.15, 1.2, 0.12, 0.12],
    [0.2, 0.15, 0.12, 2.5, 0.25],
    [0.2, 0.15, 0.12, 0.25, 1.8],
])
cost_vector = np.array([0.60, 0.40, 0.30, 0.80, 0.50])
expected_payoff = np.array([0.05, 0.10, -0.02, 0.08, 0.03])

# Solve.
w = Minimize(Variance(precision_matrix), cost_vector).value

# Render.
weights(w, labels=["A", "B", "C", "D", "E"], output_path="weights.png")
efficient_frontier(precision_matrix, cost_vector, expected_payoff, output_path="frontier.png")
cfvar_sensitivity(precision_matrix, cost_vector, expected_payoff, output_path="cfvar_alpha.png")
```

---

## What each chart shows

| Chart | X-axis | Y-axis | What to look for |
|---|---|---|---|
| `weights.png` | weight | instrument | Green = long, red = short. Look for concentration in one name. |
| `frontier.png` | `-CFVaR2` (risk) | expected return | The curve should bend: low alpha = low risk, low return; high alpha = higher risk, higher return. |
| `cfvar_alpha.png` | alpha (caution) | `-CFVaR2` (risk) | Should rise as alpha increases (more cautious = more risk-averse weights = lower risk). |

---

## What can go wrong

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'matplotlib'` | Optional dep not installed. | `pip install '.[viz]'` (or just matplotlib). |
| Empty PNG | `precision_matrix` is singular. | Add noise: `Q + 0.1 * I`. |
| Frontier has only one point | All alphas converged to the same weights. | Check that `expected_payoff` is non-uniform. |

---

## Where to look next

- **[API Reference](../api-reference.md)** — All plot functions.
- **[from-CSV tutorial](from-csv.md)** — Loading inputs.
- **[Constraints tutorial](constraints.md)** — Adding real-world
  constraints before plotting.
