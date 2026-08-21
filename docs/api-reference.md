# API Reference

Every public symbol in Convexfolio, with examples.

> 📖 **New to Python or finance?** Start with
> [Getting Started](getting-started.md) and the
> [Glossary](glossary.md). Come back here once you can read a
> simple Python script.
>
> **Looking for the 30-second version?** Jump to
> [The five classes you actually need](#the-five-classes-you-actually-need).

---

## Table of contents

- [The five classes you actually need](#the-five-classes-you-actually-need)
- [Common recipes](#common-recipes)
- [Module layout](#module-layout)
- [Configuration](#configuration)
- [Math primitives (low-level)](#math-primitives-low-level)
- [Risk evaluation](#risk-evaluation)
- [Optimisation](#optimisation)
- [Section 2.4 — determined quantities](#section-24--determined-quantities)
- [Determinism & pipeline](#determinism--pipeline)
- [CLI Reference](#cli-reference)

---

## The five classes you actually need

If you only ever use five things from this package, use these:

| Class | One-liner |
|---|---|
| `Minimize(Variance(Q), v)` | Closed-form variance minimisation. The most common call. |
| `CFVaR2Closed(Q, u, v, alpha)` | Closed-form CFVaR2 weight solver. Sharper risk measure. |
| `CFVaR2nd(alpha, u, Q, x)` | Evaluate the CFVaR2 risk number at a given weight vector. |
| `Experiment` / `load(path)` | The configuration object and how to load it. |
| `reproduce(experiment)` | End-to-end pipeline that runs everything and returns a JSON-serialisable dict. |

The rest of this page covers every other public symbol.

---

## Common recipes

### Recipe 1: minimise variance

```python
import numpy as np
from convexfolio import Variance, Minimize

Q = np.array([[2.0, 0.1], [0.1, 1.5]])   # precision matrix
v = np.array([0.60, 0.40])                 # option prices

weights = Minimize(Variance(Q), v).value
```

### Recipe 2: minimise CFVaR2

```python
from convexfolio import CFVaR2Closed

u = np.array([0.05, 0.10])                  # expected payoffs
alpha = 0.05                                # cautiousness

weights = CFVaR2Closed(Q, u, v, alpha).value
```

### Recipe 3: evaluate risk at a given weight vector

```python
from convexfolio import CFVaR2nd

risk = CFVaR2nd(alpha, u, Q, weights).value
```

### Recipe 4: full pipeline (run everything, get a dict)

```python
from convexfolio import Experiment, reproduce

report = reproduce(Experiment())
# report["outputs"]["variance_weights"] is a list of floats
# report["outputs"]["cfvar2_weights"] is a list of floats
# report["outputs"]["cfvar3_weights"] is a list of floats
```

### Recipe 5: load a config file

```python
from convexfolio import load

config = load("config.json")      # or config.yaml, or load(None) for defaults
```

---

## Module layout

| Module | Contents |
|---|---|
| `convexfolio.config` | `Experiment`, `Runtime`, `Optimization`, `load`, `validate` |
| `convexfolio.math` | Risk, optimisation, and section-2.4 primitives |
| `convexfolio.determinism` | `check` |
| `convexfolio.pipeline` | `run_and_save` |
| `convexfolio.utils` | `Logger`, `Report`, `reproduce` |

---

## Configuration

### `Experiment` (frozen dataclass)

**What it is:** The top-level configuration object. Holds everything
the pipeline needs to run.

```python
@dataclass(frozen=True)
class Experiment:
    runtime: Runtime = field(default_factory=Runtime)
    optimization: Optimization = field(default_factory=Optimization)
```

A *frozen* dataclass means it can't be changed after creation — so a
config you pass in can't quietly mutate mid-run.

### `Runtime` (frozen dataclass)

| Field | Type | Default | Plain English |
|---|---|---|---|
| `seed` | `int` | `7` | Starting number for the random number generator. |
| `log_level` | `str` | `"INFO"` | How chatty to be: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `output_directory` | `str` | `"artifacts"` | Folder where reports are saved. |

### `Optimization` (frozen dataclass)

| Field | Type | Default | Plain English |
|---|---|---|---|
| `alpha` | `float` | `0.05` | How cautious the optimiser is. Between 0 and 0.5. |
| `method` | `str` | `"all"` | Which solver to run. |
| `enforce_nu_greater_than_six` | `bool` | `True` | Refuse to run if math parameters are weird. |

### `load(path: str | None) -> Experiment`

**What it does:** Reads a config file and returns an `Experiment`.

**Parameters:**

- `path` — Path to a `.json`, `.yaml`, or `.yml` file. Pass `None`
  for defaults.

**Returns:** The loaded `Experiment` (already validated).

**Raises:** `FileNotFoundError`, `json.JSONDecodeError`,
`yaml.YAMLError`, or `ValueError` (alpha out of range).

```python
from convexfolio.config import load
config = load("config.json")
config = load(None)                  # use defaults
```

### `validate(config: Experiment) -> None`

**What it does:** Enforces semantic constraints on a config. Raises
`ValueError` if alpha is outside `(0, 0.5)`. Called automatically by
`load`.

---

## Math primitives (low-level)

These are small reusable pieces. Most users won't touch them
directly — they're the building blocks the optimisers use.

### `Compute(degrees_of_freedom)`

**What it is:** Computes the skew-t coefficient `c`.

**Parameters:**

- `degrees_of_freedom` (`float`) — `ν > 1` for the coefficient to
  exist.

**Attribute:** `.value` — the numeric coefficient.

```python
from convexfolio import Compute
c = Compute(degrees_of_freedom=8.0).value
```

### `Linear(covariance, skewness)`

**What it is:** Computes the linear bias vector `h`.

**Parameters:**

- `covariance` — 2-D covariance matrix `Σ`.
- `skewness` — 1-D skewness vector `ω`.

**Attribute:** `.value` — the 1-D bias vector.

### `Curvature(third_derivative, h)`

**What it is:** Computes the curvature vector `q`.

**Parameters:**

- `third_derivative` — 3-D tensor `Γ` of shape `(m, n, n)`.
- `h` — 1-D bias vector.

**Attribute:** `.values` — 1-D vector of length `m`.

### `Bilinear(delta_matrix, budget_matrix, covariance, third_derivative, h)`

**What it is:** Computes the bilinear expansion matrix.

**Attribute:** `.matrix` — 2-D matrix.

### `Cross(...)`

**What it is:** Same constructor as `Bilinear`; returns the transpose.

**Attribute:** `.matrix` — 2-D cross-term matrix.

### `Expect(expected_payoff, weights)`

**What it is:** Computes the expected payoff `uᵀx`.

**Attribute:** `.value` — scalar expected payoff.

### `Quadratic(precision_matrix, weights)`

**What it is:** Computes the variance `0.5 x�Qx`.

**Attribute:** `.value` — scalar variance.

### `Variance(precision_matrix)`

**What it is:** A callable variance objective. Stores `Q`; calling
`variance(weights)` returns `0.5 xᵀQx`. Compose with
`Minimize(Variance(Q), c)` to get the closed-form minimum-variance
weights.

```python
from convexfolio import Variance
variance = Variance(precision_matrix=np.eye(3))
val = variance(np.array([1.0, -2.0, 0.5]))
```

### `Cumulant(...)`

**What it is:** Computes the third central moment (skewness
correction).

**Attribute:** `.value` — scalar third cumulance.

---

## Risk evaluation

### `CFVaR2nd(alpha, expected_payoff, precision_matrix, weights)`

**What it is:** Evaluates the **second-order** CFVaR risk number at a
given weight vector. Pure function — no optimisation, just evaluation.

**Parameters:**

- `alpha` (`float`) — confidence level in `(0, 0.5)`.
- `expected_payoff` (`FloatArray`) — vector `u`.
- `precision_matrix` (`FloatArray`) — matrix `Q`.
- `weights` (`FloatArray`) — vector `x`.

**Attribute:** `.value` — scalar CFVaR2 risk number.

```python
from convexfolio import CFVaR2nd
risk = CFVaR2nd(alpha=0.05, expected_payoff=u, precision_matrix=Q, weights=x).value
```

### `CFVaR3rd(alpha, expected_payoff, precision_matrix, weights, cumulant)`

**What it is:** Evaluates the **third-order** CFVaR (with skewness
correction) at a given weight vector.

**Parameters:** Same as `CFVaR2nd` plus `cumulant` (`float`) — the
third cumulance, from `Cumulant(...).value`.

**Attribute:** `.value` — scalar CFVaR3 risk number.

---

## Optimisation

### `Minimize(variance: Variance, cost_vector)`

**What it is:** Closed-form variance minimisation under the budget
constraint. The most common call in this package.

**Parameters:**

- `variance` — a `Variance(Q)` instance.
- `cost_vector` — 1-D cost vector `v`.

**Attribute:** `.value` — the optimal weights `x*` such that
`x*ᵀ v = 1` and variance is minimised.

```python
from convexfolio import Variance, Minimize
weights = Minimize(Variance(Q), v).value
assert abs(weights.T @ v - 1.0) < 1e-8     # budget holds
```

### `Loss(coeff_a, coeff_b, coeff_c)`

**What it is:** A quadratic function `aε² + bε + c`. Internal helper
for the epsilon-star solver.

**Callable:** `loss(epsilon) -> float`.

### `Score(coeff_a, coeff_b, coeff_c, z_score)`

**What it is:** CFVaR2 upper-bound score at `ε`. Returns `+inf` when
the loss becomes non-positive (constraint violation).

### `OptimalEpsilon(alpha, expected_payoff, cost_vector, precision_matrix)`

**What it is:** Computes the optimal Lagrange multiplier `ε*`. Uses
closed-form roots from Appendix B; falls back to bounded numerical
search if roots fail.

**Attribute:** `.value` — the optimal `ε*`.

### `CFVaR2Closed(precision_matrix, expected_payoff, cost_vector, alpha)`

**What it is:** Closed-form CFVaR2 weight solver. Computes the
weights that minimise CFVaR2 using a formula (no iteration).

**Parameters:**

- `precision_matrix` (`FloatArray`) — `Q`.
- `expected_payoff` (`FloatArray`) — `u`.
- `cost_vector` (`FloatArray`) — `v`.
- `alpha` (`float`) — confidence level in `(0, 0.5)`.

**Attribute:** `.value` — closed-form optimal weights `x*`.

```python
from convexfolio import CFVaR2Closed
weights = CFVaR2Closed(precision_matrix=Q, expected_payoff=u,
                       cost_vector=v, alpha=0.05).value
```

### `CFVaR3Numerical(cost_vector, initial_weights, objective_callable)`

**What it is:** Numerical CFVaR3 weight solver. Uses SciPy's SLSQP
under the hood. Slower than closed-form but more accurate.

**Parameters:**

- `cost_vector` (`FloatArray`) — `v`.
- `initial_weights` (`FloatArray`) — starting point for the solver.
- `objective_callable` — a callable `f(x) -> float` returning the
  CFVaR3 value (typically a `CFVaR3Objective` instance).

**Attribute:** `.value` — the numerical optimal weights `x*`.

```python
from convexfolio import CFVaR3Numerical, CFVaR3Objective
objective = CFVaR3Objective(
    alpha=0.05, expected_payoff=u, precision_matrix=Q,
    kappa3_callback=lambda x: 0.0,
)
weights = CFVaR3Numerical(
    cost_vector=v,
    initial_weights=v / float(v @ v),          # feasible starting point
    objective_callable=objective,
).value
```

### `CFVaR3Objective(alpha, expected_payoff, precision_matrix, kappa3_callback)`

**What it is:** A callable that returns the CFVaR3 objective value at
any weight vector. Wraps `CFVaR3rd` so you can pass it to
`CFVaR3Numerical` (or any SciPy optimiser).

**Parameters:**

- `alpha` (`float`).
- `expected_payoff` (`FloatArray`).
- `precision_matrix` (`FloatArray`).
- `kappa3_callback` — a callable `f(weights) -> float` returning
  the third cumulance.

**Callable:** `objective(weights) -> float`.

### `QualityScore(alpha, expected_payoff, cost_vector, precision_matrix)`

**What it is:** Sanity-checks the CFVaR2 closed-form solver by
returning the CFVaR2 risk number at the closed-form optimum. Useful
for testing.

**Attribute:** `.value` — float.

---

## Section 2.4 — determined quantities

These build the precision matrix `Q` from raw option Greeks data.

### `Greeks(weights, price_drift, delta_matrix, third_derivative)`

**What it is:** Computes first-, second-, and third-order portfolio
Greeks (`theta`, `delta`, `gamma`).

**Attributes:** `.theta` (float), `.delta` (vector), `.gamma`
(matrix).

### `PortfolioVariance(gamma_matrix, delta_vector, expected_payoff, covariance, degrees_of_freedom, c_coefficient, h)`

**What it is:** Direct scalar portfolio-variance formula (section 2.4
of the paper).

**Attribute:** `.value` — scalar variance.

### `Linearize(price_drift, delta_matrix, third_derivative, expected_payoff, covariance, degrees_of_freedom, skewness, time_increment)`

**What it is:** Builds the linearised expected-return vector `u` and
precision matrix `Q` for the section-2.4 problem.

**Attributes:** `.dual_residual` (vector `u`), `.precision_matrix`
(matrix `Q`).

### `Reconstruct(price_drift, delta_matrix, third_derivative, expected_payoff, covariance, degrees_of_freedom, skewness)`

**What it is:** Recovers symmetric `Q` by evaluating portfolio
variance at basis vectors and pairwise sums.

**Attribute:** `.value` — 2-D precision matrix `Q`.

---

## Determinism & pipeline

### `check(config: Experiment, repetitions: int = 2) -> Report`

**What it does:** Runs `reproduce(config)` repeatedly and returns a
`Report` describing whether the runs were byte-identical. Uses a
process pool when `repetitions ≥ OPTIONS_PARALLEL_THRESHOLD` (default
4).

```python
from convexfolio import check
report = check(experiment, repetitions=3)
assert report.deterministic is True
```

### `run_and_save(experiment: Experiment, output_dir: str) -> Path`

**What it does:** Runs a determinism check (3 repetitions) and
persists the resulting `Report` to `output_dir/report.json`. Returns
the written path.

### `reproduce(experiment: Experiment) -> dict`

**What it does:** End-to-end pipeline — runs variance minimisation,
CFVaR2, and CFVaR3 once on a synthetic 5-instrument portfolio and
returns a JSON-serialisable dict. The `dict` has keys: `config`,
`inputs`, `outputs`, `uncertainty`.

```python
from convexfolio import Experiment, reproduce
report = reproduce(Experiment())
# report["outputs"]["variance_weights"] -> list[float]
# report["outputs"]["cfvar2_weights"]   -> list[float]
# report["outputs"]["cfvar3_weights"]   -> list[float]
# report["outputs"]["cfvar2_at_variance_weights"] -> float
```

### `Report`

Determinism result over repeated pipeline runs.

| Attribute / Property | Type | Plain English |
|---|---|---|
| `.config` | `Experiment` | The config used. |
| `.repetitions` | `int` | Number of repetitions performed. |
| `.results` | `list[dict]` | Per-run result dicts. |
| `.serialized` | `list[str]` | JSON forms of `results`. |
| `.all_match` | `bool` | Whether every run was byte-equivalent to the first. |
| `.summary` | `dict` | Public summary (safe to `json.dumps`). |
| `.deterministic` | `bool` | View of `summary["deterministic"]`. |
| `.seed` | `int` | View of `summary["seed"]`. |
| `.reference` | `dict` | Reference run (the first one). |
| `.save(path)` | `Path` | Persist `summary` as JSON. |

### `Logger(level: str, name: str = "convexfolio")`

Logging facade over Python's `logging` module. Methods: `.debug()`,
`.info()`, `.warning()`, `.error()`.

---

## CLI Reference

The CLI is installed as the `convexfolio` command.

### Commands

#### `reproduce-report`

Run the pipeline and save a JSON report to disk.

```bash
convexfolio --command reproduce-report [--config CONFIG]
```

Default output: `artifacts/report.json`.

#### `print-report`

Run the pipeline and print the report to the terminal.

```bash
convexfolio --command print-report [--config CONFIG]
```

#### `validate-determinism`

Run the pipeline N times and verify the runs are byte-identical.

```bash
convexfolio --command validate-determinism [--repetitions N] [--config CONFIG]
```

Exits with code `2` if the runs don't match.

### Options

| Option | Default | Description |
|---|---|---|
| `--config` | `None` | Path to a JSON or YAML config file. |
| `--command` | `reproduce-report` | Which command to run. |
| `--repetitions` | `3` | Repetitions for `validate-determinism`. |
