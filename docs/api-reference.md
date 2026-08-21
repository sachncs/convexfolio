# Convexfolio API Reference

The Convexfolio package exports a class-based API for option-portfolio
optimization. Each numerical routine lives in a concrete class;
instantiation captures deterministic inputs and `.value` (or a named
attribute) holds the result.

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

Top-level configuration that nests `runtime` and `optimization`.

```python
@dataclass(frozen=True)
class Experiment:
    runtime: Runtime = field(default_factory=Runtime)
    optimization: Optimization = field(default_factory=Optimization)
```

### `Runtime` (frozen dataclass)

| Field | Type | Default | Description |
|---|---|---|---|
| `seed` | `int` | `7` | Random seed passed to numpy. |
| `log_level` | `str` | `"INFO"` | stdlib `logging` level name. |
| `output_directory` | `str` | `"artifacts"` | Directory for saved reports. |

### `Optimization` (frozen dataclass)

| Field | Type | Default | Description |
|---|---|---|---|
| `alpha` | `float` | `0.05` | Confidence level in `(0, 0.5)`. |
| `method` | `str` | `"all"` | Optimization method selector. |
| `enforce_nu_greater_than_six` | `bool` | `True` | Whether to enforce `nu > 6`. |

### `load(path: str | None) -> Experiment`

Load an `Experiment` from a JSON (`.json`) or YAML (`.yaml`, `.yml`)
file. Pass `None` for defaults.

```python
from convexfolio.config import load
config = load("config.json")      # or load(None) for defaults
```

Raises `FileNotFoundError`, `json.JSONDecodeError`, `yaml.YAMLError`, or
`ValueError` (invalid alpha).

### `validate(config: Experiment) -> None`

Enforce semantic constraints. Raises `ValueError` if
`config.optimization.alpha` is outside `(0, 0.5)`.

---

## Math primitives (low-level building blocks)

### `Compute(degrees_of_freedom: float)`

Skew-t coefficient `c` (Eq. for the `nu`-degrees-of-freedom skew-t).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The numeric coefficient. |

```python
from convexfolio import Compute
c = Compute(degrees_of_freedom=8.0).value
```

### `Linear(covariance, skewness)`

Linear bias vector `h = Σω / sqrt(1 + ωᵀΣω)`.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `FloatArray` | The 1-D bias vector. |

### `Curvature(third_derivative, h)`

Curvature vector `q_m = hᵀ Γ^[m] h` for each instrument `m`.

| Attribute | Type | Description |
|---|---|---|
| `.values` | `FloatArray` | 1-D vector of length `m`. |

### `Bilinear(delta_matrix, budget_matrix, covariance, third_derivative, h)`

Bilinear expansion matrix `(D + Bᵀ)ᵀ Σ [Γ^[1]h, …, Γ^[M]h]`.

| Attribute | Type | Description |
|---|---|---|
| `.matrix` | `FloatArray` | The 2-D bilinear expansion matrix. |

### `Cross(...)`

Cross-term matrix — transpose of `Bilinear(...).matrix`. Same constructor.

| Attribute | Type | Description |
|---|---|---|
| `.matrix` | `FloatArray` | The 2-D cross-term matrix. |

### `Expect(expected_payoff, weights)`

Portfolio expected payoff `uᵀ x`.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar expected payoff. |

### `Quadratic(precision_matrix, weights)`

Portfolio variance `0.5 xᵀ Q x`.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar variance. |

### `Variance(precision_matrix)`

Callable variance objective. Stores the precision matrix `Q`; calling
`variance(weights)` returns `0.5 xᵀ Q x`. Compose with
`Minimize(Variance(Q), c)` to obtain the closed-form minimum-variance
weights.

```python
from convexfolio import Variance
variance = Variance(precision_matrix=np.eye(3))
val = variance(np.array([1.0, -2.0, 0.5]))
```

### `Cumulant(weights, degrees_of_freedom, pricing_vector, residual_matrix, delta_matrix, budget_matrix, covariance, tau)`

Third central moment (Eq. S2.Ex24–S2.Ex26).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar third cumulance. |

---

## Risk evaluation

### `CFVaR2nd(alpha, expected_payoff, precision_matrix, weights)`

Second-order conditional fractional Value-at-Risk (Eq. S2.Ex22).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar CFVaR2 risk number. |

```python
from convexfolio import CFVaR2nd
risk = CFVaR2nd(
    alpha=0.05,
    expected_payoff=u,
    precision_matrix=Q,
    weights=x,
).value
```

### `CFVaR3rd(alpha, expected_payoff, precision_matrix, weights, cumulant)`

Third-order CFVaR (Eq. S2.Ex23) including the third-cumulance skewness
correction.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar CFVaR3 risk number. |

---

## Optimisation

### `Minimize(variance: Variance, cost_vector)`

Closed-form variance minimisation under budget `cᵀ x = 1`.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `FloatArray` | The optimal weights `x*`. |

```python
from convexfolio import Variance, Minimize
weights = Minimize(Variance(Q), c).value
assert np.isclose(weights.T @ c, 1.0, atol=1e-8)
```

### `Loss(coeff_a, coeff_b, coeff_c)`

Quadratic variance term. Callable: `loss(ε) = aε² + bε + c`.

### `Score(coeff_a, coeff_b, coeff_c, z_score)`

CFVaR2 upper-bound score at `ε`. Callable; returns `+inf` when the loss
is non-positive (constraint violation).

### `OptimalEpsilon(alpha, expected_payoff, cost_vector, precision_matrix)`

Compute the optimal Lagrange multiplier. Closed-form roots from Appendix
B; bounded numerical fallback if root conditions fail.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The optimal `ε*`. |

### `CFVaR2Closed(precision_matrix, expected_payoff, cost_vector, alpha)`

Closed-form CFVaR2 weight solver (Eq. 5–6 for P2 with the determined
`ε*`).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `FloatArray` | The closed-form optimal weights `x*`. |

```python
from convexfolio import CFVaR2Closed
weights = CFVaR2Closed(
    precision_matrix=Q,
    expected_payoff=u,
    cost_vector=v,
    alpha=0.05,
).value
assert np.isclose(weights.T @ v, 1.0, atol=1e-8)
```

### `CFVaR3Numerical(cost_vector, initial_weights, objective_callable)`

Numerical CFVaR3 weight solver. Solves `min cfvar3(x) s.t. xᵀ v = 1` via
`scipy.optimize.minimize` (SLSQP).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `FloatArray` | The numerical optimal weights `x*`. |

```python
from convexfolio import CFVaR3Numerical, CFVaR3Objective
objective = CFVaR3Objective(
    alpha=0.05, expected_payoff=u, precision_matrix=Q,
    kappa3_callback=lambda x: 0.0,
)
weights = CFVaR3Numerical(
    cost_vector=v,
    initial_weights=np.ones_like(v) / v.sum(),
    objective_callable=objective,
).value
```

### `CFVaR3Objective(alpha, expected_payoff, precision_matrix, kappa3_callback)`

Callable CFVaR3 objective for `scipy.optimize` solvers. Wraps
`CFVaR3rd(...)` so that `objective(x) -> float` returns the third-order
CFVaR at `x` with the third cumulance supplied by `kappa3_callback`.

### `QualityScore(alpha, expected_payoff, cost_vector, precision_matrix)`

Sanity-check the CFVaR2 closed-form solver by returning the CFVaR2 risk
number at the closed-form weights.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The CFVaR2 risk number at the closed-form optimum. |

---

## Section 2.4 — determined quantities

### `Greeks(weights, price_drift, delta_matrix, third_derivative)`

First-, second-, and third-order portfolio Greeks.

| Attribute | Type | Description |
|---|---|---|
| `.theta` | `float` | Scalar `θ`. |
| `.delta` | `FloatArray` | 1-D `δ` vector. |
| `.gamma` | `FloatArray` | 2-D `Γ` matrix. |

### `PortfolioVariance(gamma_matrix, delta_vector, expected_payoff, covariance, degrees_of_freedom, c_coefficient, h)`

Direct scalar portfolio-variance formula (Section 2.4).

| Attribute | Type | Description |
|---|---|---|
| `.value` | `float` | The scalar variance. |

### `Linearize(price_drift, delta_matrix, third_derivative, expected_payoff, covariance, degrees_of_freedom, skewness, time_increment)`

Builds linearised `u` and `Q` for the section-2.4 problem.

| Attribute | Type | Description |
|---|---|---|
| `.dual_residual` | `FloatArray` | Linearised expected return `u`. |
| `.precision_matrix` | `FloatArray` | Linearised precision matrix `Q`. |

### `Reconstruct(price_drift, delta_matrix, third_derivative, expected_payoff, covariance, degrees_of_freedom, skewness)`

Recovers symmetric `Q` by evaluating portfolio variance at basis vectors
and pairwise sums.

| Attribute | Type | Description |
|---|---|---|
| `.value` | `FloatArray` | The 2-D reconstructed precision matrix `Q`. |

---

## Determinism & pipeline

### `check(config: Experiment, repetitions: int = 2) -> Report`

Run `reproduce(config)` repeatedly (process pool when `repetitions ≥
OPTIONS_PARALLEL_THRESHOLD`, default 4) and return a `Report`.

```python
from convexfolio import check
report = check(experiment, repetitions=3)
assert report.deterministic is True
```

### `run_and_save(experiment: Experiment, output_dir: str) -> Path`

Run a determinism check (3 repetitions) and persist the resulting
`Report` to `output_dir/report.json`. Returns the written path.

### `reproduce(experiment: Experiment) -> dict`

Run the end-to-end optimisation once and return the structured report
(`config`, `inputs`, `outputs`, `uncertainty` keys). Uses synthetic
matrices as a self-contained smoke pipeline.

### `Report`

Determinism result over repeated pipeline runs.

| Attribute / Property | Type | Description |
|---|---|---|
| `.config` | `Experiment` | The configuration used. |
| `.repetitions` | `int` | Number of repetitions performed. |
| `.results` | `list[dict]` | Per-run result dicts. |
| `.serialized` | `list[str]` | JSON-serialised forms of `results`. |
| `.all_match` | `bool` | Whether every run was byte-equivalent to the first. |
| `.summary` | `dict` | Public summary dict (safe to `json.dumps`). |
| `.deterministic` | `bool` | View of `summary["deterministic"]`. |
| `.seed` | `int` | View of `summary["seed"]`. |
| `.reference` | `dict` | Reference report (the first run). |
| `.save(path)` | `Path` | Persist `summary` as JSON. |

### `Logger(level: str, name: str = "convexfolio")`

Logging facade over the stdlib `logging` module. Methods: `.debug()`,
`.info()`, `.warning()`, `.error()`.

---

## CLI Reference

The CLI entry point is installed as the `convexfolio` command when the
package is installed.

### Commands

#### `reproduce-report`

Generate and save a reproduction report.

```bash
convexfolio --command reproduce-report [--config CONFIG]
```

#### `print-report`

Print the reproduction report to stdout.

```bash
convexfolio --command print-report [--config CONFIG]
```

#### `validate-determinism`

Validate that the package produces deterministic results.

```bash
convexfolio --command validate-determinism [--repetitions N] [--config CONFIG]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--config` | None | Path to JSON or YAML config file. |
| `--command` | `reproduce-report` | Command to execute. |
| `--repetitions` | `3` | Number of repetitions for determinism validation. |
