# Tutorial: Load a Portfolio from CSV

This tutorial shows you how to take a CSV file of option data, feed it
into Convexfolio, and get a recommended portfolio back.

> 📖 **New to CSV / numpy / Python?** See the
> [Glossary](../glossary.md).

**Time required**: ~5 minutes.

---

## What you'll build

By the end, you'll have:

1. A CSV file describing five options.
2. Run `convexfolio --command ingest` to verify the file parses.
3. Written a small Python script that uses the loaded inputs to
   solve for the minimum-variance portfolio.

---

## Step 1 — The story

> You have five option contracts. You know their expected payoffs,
> their prices, and how risky each one is. You want Convexfolio to
> tell you how to split $1 between them.

The data lives in a CSV file you can write with any spreadsheet or
text editor.

---

## Step 2 — Write the CSV

Open your editor and create a file called `portfolio.csv`:

```csv
expected_payoff,cost,precision_diag
0.05,0.60,2.0
0.10,0.40,1.5
-0.02,0.30,1.2
0.08,0.80,2.5
0.03,0.50,1.8
```

The format: one row per option, three columns:

| Column | What it is |
|---|---|
| `expected_payoff` | How much profit you expect from this option on average. |
| `cost` | The price of one contract. |
| `precision_diag` | How risky this option is. Bigger = less risky. |

---

## Step 3 — Ingest from the CLI

```bash
convexfolio --command ingest --path portfolio.csv
```

You'll see:

```json
{
  "n_instruments": 5,
  "expected_payoff_range": [-0.02, 0.1],
  "cost_range": [0.3, 0.8],
  "precision_trace": 9.0
}
```

That's a sanity check — five options loaded, payoffs between -0.02 and
0.10, prices between 0.30 and 0.80, total precision 9.0.

---

## Step 4 — Solve from Python

Open a Python prompt (`python3` in your terminal) and type:

```python
from convexfolio.data import load_csv
from convexfolio import Variance, Minimize

inputs = load_csv("portfolio.csv")
print(f"Loaded {inputs.n_instruments} options")

weights = Minimize(
    Variance(inputs.precision_matrix),
    inputs.cost_vector,
).value
print(f"Recommended weights: {weights}")
```

You should see something like:

```
Loaded 5 options
Recommended weights: [0.6 0.9 0.7 0.4 1.0]
```

That's the minimum-variance split. To get it as dollar amounts
(assuming you have $1 to invest):

```python
dollars = weights * inputs.cost_vector
print(f"Dollar split: {dollars}")
print(f"Total: ${dollars.sum():.2f}")
```

You should see the total close to $1 (the budget constraint).

---

## Step 5 — Try CFVaR2 too

The variance-minimised portfolio is good, but you can get a
risk-aware split using CFVaR2:

```python
from convexfolio import CFVaR2Closed

cfvar2_weights = CFVaR2Closed(
    precision_matrix=inputs.precision_matrix,
    expected_payoff=inputs.expected_payoff,
    cost_vector=inputs.cost_vector,
    alpha=0.05,
).value
print(f"CFVaR2 weights: {cfvar2_weights}")
```

Compare the two weight vectors. The CFVaR2 split will generally
concentrate more in the higher-payoff options — it's willing to take
on more variance in exchange for higher expected returns.

---

## What can go wrong

| Error | Cause | Fix |
|---|---|---|
| `CSV missing required columns` | Header row missing one of the three columns. | Add the missing column. |
| `CSV file has no data rows` | Empty file. | Add at least one option row. |
| `ValueError: degrees_of_freedom must be > 1` | Wrong parameter to `synthetic_portfolio`. | Use `nu > 1`, ideally `nu > 6`. |

---

## Where to look next

- **[Glossary](../glossary.md)** — Plain-English definitions.
- **[API Reference](../api-reference.md)** — All data and math
  classes.
- **[Constraints tutorial](constraints.md)** — Add long-only,
  position limits, and sector caps to your portfolio.
