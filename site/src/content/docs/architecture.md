---
title: "Architecture"
---
# Architecture

A look under the hood of Convexfolio — how the pieces fit together.
You don't need to read this to use the package. Read it if you want
to modify it, contribute to it, or just satisfy your curiosity.

> 📖 **New to the codebase?** See the
> [Glossary](/convexfolio/docs/glossary/) for terms used here.

---

## The big picture

The package does one job — solve a portfolio problem and produce a
report. Everything else is plumbing.

<div class="architecture-graph" aria-labelledby="architecture-graph-title">
  <div class="architecture-graph-heading">
    <p class="eyebrow">Runtime path</p>
    <h3 id="architecture-graph-title">From an experiment to an auditable report</h3>
    <p>Each boundary validates what it receives before handing control to the next stage. The strategy and risk branches are interchangeable implementations behind typed contracts.</p>
  </div>
  <ol class="architecture-flow">
    <li class="architecture-node architecture-node-input"><span class="architecture-step">01</span><strong>Input boundary</strong><small>Python API or CLI<br />CSV, config, prices</small></li>
    <li class="architecture-connector" aria-hidden="true"><span>normalise</span><i></i></li>
    <li class="architecture-node"><span class="architecture-step">02</span><strong>Configuration</strong><small><code>Load</code> → <code>Validate</code><br />policy and reproducibility</small></li>
    <li class="architecture-connector" aria-hidden="true"><span>construct</span><i></i></li>
    <li class="architecture-node architecture-node-contracts"><span class="architecture-step">03</span><strong>Domain contracts</strong><small><code>Vector</code> · <code>Matrix</code><br />constraints · problem</small></li>
    <li class="architecture-branch" aria-label="Polymorphic strategy branches">
      <span class="architecture-branch-label">select by contract</span>
      <div class="architecture-branch-grid">
        <span class="architecture-branch-node"><strong>RiskMeasure</strong><small>variance · CFVaR</small></span>
        <span class="architecture-branch-node"><strong>Optimizer</strong><small>closed-form · SLSQP</small></span>
        <span class="architecture-branch-node"><strong>Constraint</strong><small>budget · sector · leverage</small></span>
      </div>
    </li>
    <li class="architecture-connector" aria-hidden="true"><span>solve + check</span><i></i></li>
    <li class="architecture-node architecture-node-output"><span class="architecture-step">04</span><strong>Diagnostics + report</strong><small>feasibility, warnings,<br />versioned JSON output</small></li>
  </ol>
  <p class="architecture-graph-fallback"><strong>Reading order:</strong> input boundary → configuration → domain contracts → risk, optimizer, and constraint implementations → diagnostics and report.</p>
</div>

You give it inputs → it solves → you get a JSON report.

---

## The files in the package

Think of the package like a small restaurant.

| File | Plain-English role | Restaurant analogy |
|---|---|---|
| `cli.py` | Takes commands from the terminal. | The waiter taking your order. |
| `config.py` | Reads your settings file. | The host checking your reservation. |
| `utils.py` | Cross-cutting `Logger`, `Report`, and `Reproduce` pipeline. | The kitchen manager coordinating everything. |
| `arrays.py` | Validated, read-only `Vector` and `Matrix` value objects with `.copy()` and `.validate()`. | Measured ingredients with a safe prep copy. |
| `domain.py` | Problem, result, tolerance, and diagnostic value objects. | The order ticket and completed dish. |
| `interfaces.py` | ABC contracts for risk measures, constraints, and optimizers. | The kitchen's interchangeable stations. |
| `optimization.py` | Closed-form and SLSQP optimizer implementations. | The cooking techniques. |
| `risk.py` | Polymorphic variance and CFVaR risk implementations. | The tasting criteria. |
| `math.py` | All the numerical classes — risk, optimisation, section 2.4 primitives. | The kitchen itself. |
| `backtest.py` | Multi-period rebalancing simulator. | The dining-room host tracking turnover across courses. |
| `constraints.py` | SLSQP constraint builders (budget, long-only, sector caps). | The reservation ledger. |
| `data.py` | CSV loader, synthetic portfolio, shape summary. | The pantry supplier. |
| `hf_data.py` | Hugging Face SP500 options-IV ingestion pipeline. | The off-site delivery driver. |
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

`Experiment` is a [frozen dataclass](/convexfolio/docs/glossary/) — read-only once
created. It has two parts:

- `runtime` — execution settings (seed, log level, output directory).
- `optimization` — math settings (alpha, method, enforce_nu flag).

`Load(path)` reads a JSON or YAML file and produces an `Experiment`.
`Validate(config)` enforces constraints (e.g., `0 < alpha < 0.5`).

```python
from convexfolio import Experiment
from convexfolio.config import Load, Validate

config = Load("config.json")()    # or Load(None)() for defaults
Validate(config)                  # raises ValueError if alpha is bad
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

This runs the pipeline three times and compares the serialized reports
for equality.

---

## The CLI

The `convexfolio` command has six sub-commands:

| Command | What it does |
|---|---|
| `reproduce-report` | Run the pipeline, save the report to `output_directory/report.json`. |
| `print-report` | Run the pipeline, print the report to the terminal. |
| `validate-determinism` | Run the pipeline N times, verify serialized reports match. |
| `ingest` | Read a portfolio CSV and print its shape summary. |
| `plot` | Render selected portfolio charts. |
| `backtest` | Run a multi-period rebalance simulation from price history. |

Each accepts a `--config path/to/config.json` flag.

---

## Design principles

1. **Faithful to the paper.** The math is implemented exactly as the
   paper specifies. See [Fidelity Report](/convexfolio/docs/fidelity_report/).
2. **Class-based composition.** Small reusable pieces compose into
   the answer. No monolithic "solve everything" function.
3. **Deterministic and auditable.** Same inputs → same outputs. You
   can re-run last week's report and get the same numbers.
4. **Type-checked.** Every public symbol has type hints. Mypy runs on
   every commit.
5. **Forward-only.** No backward-compat shims. Renaming the package
   or breaking the API is acceptable when there's a real reason.

---

## Object-oriented contracts and polymorphism

The package uses small ABCs where callers need interchangeable behavior:

* `RiskMeasure.evaluate(problem)` provides a common risk calculation
  contract for variance and CFVaR implementations.
* `Constraint.residual(weights)` and `Constraint.check(weights)` provide
  named equality and inequality checks with structured diagnostics.
* `Optimizer.solve(problem)` lets closed-form and SLSQP implementations
  be selected by policy rather than by a growing conditional function.

`Vector` and `Matrix` are validated value objects. They are read-only at
the boundary, own their shape/finite-value checks, and expose explicit
`.copy()` methods when writable working storage is required. This keeps
validation and ownership rules next to the data they protect.

The design favors shallow inheritance, composition, and descriptive names:
new implementations should satisfy an existing contract before adding a
new abstraction. Failures should use the typed domain exceptions in
`errors.py`, and optimizer results should preserve iterations, messages,
and constraint diagnostics for callers.

---

## Where to look next

- **[API Reference](/convexfolio/docs/api-reference/)** — Every public symbol, with
  examples.
- **[Migration guide](/convexfolio/docs/migration/)** — Upgrade from the earlier
  helper-based API.
- **[Glossary](/convexfolio/docs/glossary/)** — Plain-English definitions of every
  term used here.
- **[Fidelity Report](/convexfolio/docs/fidelity_report/)** — Does the code match the
  paper?
- **[Mismatch Report](/convexfolio/docs/mismatch_report/)** — Known differences
  between the code and the paper.
