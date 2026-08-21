# Tutorial: Multi-Period Backtesting

This tutorial shows you how to test a portfolio strategy over a
historical price series, with periodic rebalancing and transaction
costs.

> � **New here?** See the [Glossary](../glossary.md).

**Time required**: ~10 minutes.

---

## What you'll build

By the end, you'll have:

1. A price-history CSV with daily prices for five instruments.
2. A backtest run that rebalances every two days and tracks portfolio
   value.
3. A printed summary with final value, total turnover, costs, and
   max drawdown.

---

## The story

> You have a portfolio strategy. You want to know: if I had run this
> strategy every day for a year, how would it have done?
>
> You don't have last year's prices, so we'll use a tiny synthetic
> example.

---

## Step 1 — Write the price history

Create `prices.csv`:

```csv
timestamp,A,B,C,D,E
2026-01-01,1.00,1.00,1.00,1.00,1.00
2026-01-02,1.05,0.98,1.02,0.95,1.03
2026-01-03,1.08,0.96,1.05,0.92,1.06
2026-01-04,1.04,1.02,1.08,0.98,1.10
2026-01-05,1.10,0.99,1.12,0.95,1.07
2026-01-06,1.12,1.01,1.15,0.93,1.09
2026-01-07,1.15,1.04,1.18,0.96,1.12
```

The format:

- First column: timestamp (any label).
- Remaining columns: one per instrument, prices normalised so the
  first row is 1.0.

---

## Step 2 — Run the backtest from the CLI

```bash
convexfolio --command backtest --path prices.csv --rebalance-frequency 2
```

You'll see a JSON summary printed:

```json
{
  "n_timestamps": 7,
  "n_instruments": 5,
  "rebalance_frequency": 2,
  "transaction_cost_bps": 5.0,
  "alpha": 0.05,
  "final_portfolio_value": 1.18,
  "total_turnover": 4.2,
  "total_costs": 0.002,
  "max_drawdown": 0.04
}
```

The `final_portfolio_value` is your portfolio value at the last
timestamp, starting from 1.0. `total_costs` is the cumulative
transaction cost in dollars. `max_drawdown` is the largest
peak-to-trough decline.

---

## Step 3 — Try different rebalance frequencies

```bash
# Rebalance every step (1 = daily in this example).
convexfolio --command backtest --path prices.csv --rebalance-frequency 1

# Rebalance weekly (every 5 timestamps).
convexfolio --command backtest --path prices.csv --rebalance-frequency 5
```

More frequent rebalancing → more turnover → more transaction costs.

---

## Step 4 — Add a portfolio config

If you have a config file with an `inputs` section, you can pass it
to the backtest:

```bash
convexfolio --command backtest \
    --path prices.csv \
    --config config.json \
    --rebalance-frequency 3 \
    --transaction-cost-bps 10
```

The portfolio inputs are re-scaled at each rebalance timestamp based
on the price ratio `current_price / base_price`. This keeps the
portfolio's risk characteristics comparable across rebalances.

---

## Step 5 — From Python

```python
import numpy as np
from convexfolio.backtest import (
    BacktestConfig,
    PriceHistory,
    load_price_history_csv,
    run_backtest,
)
from convexfolio.data import synthetic_portfolio

history = load_price_history_csv("prices.csv")
portfolio_inputs = synthetic_portfolio(
    n_instruments=history.n_instruments, degrees_of_freedom=8.0, seed=7
)
config = BacktestConfig(
    portfolio_inputs=portfolio_inputs,
    rebalance_frequency=2,
    transaction_cost_bps=5.0,
    alpha=0.05,
)
result = run_backtest(history, config)
print(f"Final value: {result.portfolio_value[-1]:.4f}")
print(f"Total turnover: {result.summary['total_turnover']:.4f}")
print(f"Max drawdown: {result.summary['max_drawdown']:.4f}")
```

The result has time-series arrays (`portfolio_value`, `weights`,
`turnover`, `cumulative_costs`) plus the summary dict.

---

## What can go wrong

| Error | Cause | Fix |
|---|---|---|
| `price history must have at least 2 timestamps` | CSV has fewer than 2 rows. | Add more rows. |
| `first CSV column must be 'timestamp'` | Header missing the `timestamp` column. | Add it. |
| Extreme `final_portfolio_value` (e.g. 1e10) | Numerical instability in the solver on rescaled inputs. | Use a tighter rebalance frequency, or add long-only constraints via the constraints module. |

---

## Where to look next

- **[Constraints tutorial](constraints.md)** — Add long-only to
  stabilise backtest results.
- **[API Reference](../api-reference.md)** — Full backtest API.
- **[from-CSV tutorial](from-csv.md)** — Loading portfolio inputs.
