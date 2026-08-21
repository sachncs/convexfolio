# Architecture

A look under the hood of Convexfolio — how the pieces fit together.
You don't need to read this to use the package. Read it if you want
to modify it, contribute to it, or just satisfy your curiosity.

> 📖 **New to the codebase?** See the
> [Glossary](glossary.md) for terms used here.

---

## The big picture

The package does one job — solve a portfolio problem and produce a
report. Everything else is plumbing.

```
            ┌──────────────────────────┐
            │  You (Python or CLI)     │
            └─────────────┬────────────┘
                          │ give inputs
                          ▼
            ┌──────────────────────────┐
            │  config.py               │  ← reads config.json / .yaml
            │  + utils.Logger          │  ← prints progress
            └─────────────�────────────┘
                          │ loads
                          ▼
            ┌──────────────────────────┐
            │  utils.reproduce()       │  ← the pipeline
            │   ├─ Variance / CFVaR2   │     (the math)
            │   ├─ Minimize / SLSQP    │
            │   └─ Risk evaluators     │
            └─────────────┬────────────┘
                          │ produces
                          ▼
            ┌──────────────────────────┐
            │  JSON report             │
            │  (printed or saved)      │
            └──────────────────────────┘
```

You give it inputs → it solves → you get a JSON report.

---

## The files in the package

Think of the package like a small restaurant.

| File | Plain-English role | Restaurant analogy |
|---|---|---|
| `cli.py` | Takes commands from the terminal. | The waiter taking your order. |
| `config.py` | Reads your settings file. | The host checking your reservation. |
| `utils.py` | Glue code: logger, report object, the main `reproduce()` pipeline. | The kitchen manager coordinating everything. |
| `math.py` | All the numerical classes — risk, optimisation, section 2.4 primitives. | The kitchen itself. |
| `pipeline.py` | Runs the determinism check and saves the report. | The cashier writing the receipt. |
| `determinism.py` | Runs the pipeline multiple times to verify it produces identical results. | The quality-control inspector. |
| `types.py` | Type aliases (`FloatArray`). | A shared dictionary of cooking terms. |
| `__init__.py` | The list of things the package exports. | The menu. |

---

## The math classes

`math.py` contains the meat of the package. It's organised into four
groups, each with a clear job.

### Low-level primitives

These are the small, reusable pieces other classes build on.

- `Compute` — the skew-t coefficient `c` (a scalar).
- `Linear` — the linear bias vector `h`.
- `Curvature` — the curvature vector `q`.
- `Bilinear`, `Cross` — section-2.4 expansion matrices.
- `Expect` — expected payoff `uᵀx`.
- `Quadratic` — variance `0.5 xᵀQx`.
- `Variance` — a callable variance objective you can plug into
  `Minimize`.
- `Cumulant` — the third central moment.

You probably won't use these directly unless you're extending the
package.

### Risk evaluators

These compute a risk **number** for any given portfolio.

- `CFVaR2nd(alpha, u, Q, x)` — second-order CFVaR at weights `x`.
  Fast.
- `CFVaR3rd(alpha, u, Q, x, κ₃)` — third-order CFVaR with skewness
  correction. More accurate.

### Optimisers

These compute the **weights** that minimise some objective.

- `Minimize(Variance(Q), c)` — closed-form variance minimisation.
  Returns weights directly via a formula.
- `CFVaR2Closed(Q, u, v, alpha)` — closed-form CFVaR2 solver. Returns
  weights via an exact formula.
- `CFVaR3Numerical(v, x0, objective)` — numerical CFVaR3 solver. Uses
  SciPy's SLSQP under the hood.
- `CFVaR3Objective(alpha, u, Q, κ₃_callback)` — a callable objective
  you pass to `CFVaR3Numerical`.

### Section 2.4 helpers

These build the precision matrix `Q` from raw option data.

- `Greeks` — portfolio Greeks (theta, delta, gamma).
- `PortfolioVariance` — direct scalar variance formula.
- `Linearize` — builds the linearised `u` and `Q` for section 2.4.
- `Reconstruct` — recovers `Q` from the portfolio variance evaluated
  at basis vectors.

---

## The configuration

`Experiment` is a [frozen dataclass](glossary.md) — read-only once
created. It has two parts:

- `runtime` — execution settings (seed, log level, output directory).
- `optimization` — math settings (alpha, method, enforce_nu flag).

`load(path)` reads a JSON or YAML file and produces an `Experiment`.
`validate(config)` enforces constraints (e.g., `0 < alpha < 0.5`).

```python
from convexfolio import Experiment, load, validate

config = load("config.json")      # or load(None) for defaults
validate(config)                  # raises ValueError if alpha is bad
```

---

## Determinism

Convexfolio guarantees **the same inputs always produce the same
outputs**. Two mechanisms:

1. **Seeded random numbers.** All randomness goes through
   `numpy.random.default_rng(seed)`. Same seed = same sequence.
2. **Frozen dataclasses.** `Experiment` and friends can't be mutated
   after creation. So a config you passed in can't quietly change
   mid-run.

You can verify with `validate-determinism`:

```bash
convexfolio --command validate-determinism --repetitions 3
```

This runs the pipeline three times and asserts the results are
byte-identical.

---

## The CLI

The `convexfolio` command has three sub-commands:

| Command | What it does |
|---|---|
| `reproduce-report` | Run the pipeline, save the report to `output_directory/report.json`. |
| `print-report` | Run the pipeline, print the report to the terminal. |
| `validate-determinism` | Run the pipeline N times, verify byte-identical output. |

Each accepts a `--config path/to/config.json` flag.

---

## Design principles

1. **Faithful to the paper.** The math is implemented exactly as the
   paper specifies. See [Fidelity Report](fidelity_report.md).
2. **Class-based composition.** Small reusable pieces compose into
   the answer. No monolithic "solve everything" function.
3. **Deterministic and auditable.** Same inputs → same outputs. You
   can re-run last week's report and get the same numbers.
4. **Type-checked.** Every public symbol has type hints. Mypy runs on
   every commit.
5. **Forward-only.** No backward-compat shims. Renaming the package
   or breaking the API is acceptable when there's a real reason.

---

## Where to look next

- **[API Reference](api-reference.md)** — Every public symbol, with
  examples.
- **[Glossary](glossary.md)** — Plain-English definitions of every
  term used here.
- **[Fidelity Report](fidelity_report.md)** — Does the code match the
  paper?
- **[Mismatch Report](mismatch_report.md)** — Known differences
  between the code and the paper.
