# API Reference

## Public API

The public API is exported from the `oop` package.

### Imports

```python
from options import (
    solve_variance_minimization,
    solve_cfvar2_closed_form,
    solve_cfvar3_numerical,
    cfvar3_objective,
    second_order_risk,
    third_order_risk,
)
```

### Functions

#### `solve_variance_minimization`

```python
def solve_variance_minimization(v: FloatArray, q_matrix: FloatArray) -> FloatArray:
```

Solve minimum variance portfolio optimization under budget constraint.

**Parameters:**
- `v` (FloatArray): Option prices vector of shape `(n,)`
- `q_matrix` (FloatArray): Covariance matrix of shape `(n, n)`

**Returns:**
- `FloatArray`: Optimal portfolio weights of shape `(n,)`

**Constraints:**
- `x^T v = 1` (budget constraint)

**Example:**
```python
import numpy as np
from options import solve_variance_minimization

q = np.array([[2.0, 0.1], [0.1, 1.5]])
v = np.array([1.2, 0.8])
weights = solve_variance_minimization(v=v, q_matrix=q)
# weights satisfies: weights @ v == 1.0
```

---

#### `solve_cfvar2_closed_form`

```python
def solve_cfvar2_closed_form(
    q_matrix: FloatArray,
    u: FloatArray,
    v: FloatArray,
    alpha: float,
) -> FloatArray:
```

Solve CFVaR2 portfolio optimization using closed-form solution.

**Parameters:**
- `q_matrix` (FloatArray): Covariance matrix of shape `(n, n)`
- `u` (FloatArray): Expected returns vector of shape `(n,)`
- `v` (FloatArray): Option prices vector of shape `(n,)`
- `alpha` (float): Risk parameter (0 < alpha < 0.5)

**Returns:**
- `FloatArray`: Optimal portfolio weights of shape `(n,)`

**Example:**
```python
import numpy as np
from options import solve_cfvar2_closed_form

q = np.array([[2.5, 0.0], [0.0, 1.5]])
u = np.array([0.1, 0.3])
v = np.array([1.0, 2.0])
weights = solve_cfvar2_closed_form(q_matrix=q, u=u, v=v, alpha=0.05)
```

---

#### `solve_cfvar3_numerical`

```python
def solve_cfvar3_numerical(
    v: FloatArray,
    initial_x: FloatArray,
    objective_callable: Callable[[np.ndarray], float],
) -> FloatArray:
```

Solve CFVaR3 portfolio optimization using numerical methods.

**Parameters:**
- `v` (FloatArray): Option prices vector of shape `(n,)`
- `initial_x` (FloatArray): Initial guess of shape `(n,)`
- `objective_callable` (Callable): Objective function to minimize

**Returns:**
- `FloatArray`: Optimal portfolio weights of shape `(n,)`

---

#### `cfvar3_objective`

```python
def cfvar3_objective(
    alpha: float,
    u: FloatArray,
    q_matrix: FloatArray,
    kappa3_callback: Callable[[np.ndarray], float],
) -> Callable[[np.ndarray], float]:
```

CFVaR3 objective function for numerical optimization.

**Parameters:**
- `alpha` (float): Risk parameter
- `u` (FloatArray): Expected returns vector
- `q_matrix` (FloatArray): Covariance matrix
- `kappa3_callback` (Callable): Third-order cumulant function

**Returns:**
- `Callable`: Objective function compatible with `solve_cfvar3_numerical`

---

#### `second_order_risk`

```python
def second_order_risk(
    alpha: float,
    u: FloatArray,
    q_matrix: FloatArray,
    x: FloatArray,
) -> float:
```

Calculate CFVaR2 for a given portfolio.

**Parameters:**
- `alpha` (float): Risk parameter
- `u` (FloatArray): Expected returns vector
- `q_matrix` (FloatArray): Covariance matrix
- `x` (FloatArray): Portfolio weights

**Returns:**
- `float`: CFVaR2 value

---

#### `third_order_risk`

```python
def third_order_risk(
    alpha: float,
    u: FloatArray,
    q_matrix: FloatArray,
    x: FloatArray,
    third_order_cumulant: float,
) -> float:
```

Calculate CFVaR3 for a given portfolio.

**Parameters:**
- `alpha` (float): Risk parameter
- `u` (FloatArray): Expected returns vector
- `q_matrix` (FloatArray): Covariance matrix
- `x` (FloatArray): Portfolio weights
- `third_order_cumulant` (float): Third-order cumulant

**Returns:**
- `float`: CFVaR3 value

## CLI Reference

### Commands

#### `reproduce-report`

Generate and save a reproduction report.

```bash
options --command reproduce-report [--config CONFIG]
```

#### `print-report`

Print the reproduction report to stdout.

```bash
options --command print-report [--config CONFIG]
```

#### `validate-determinism`

Validate that the package produces deterministic results.

```bash
options --command validate-determinism [--repetitions N] [--config CONFIG]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--config` | None | Path to JSON config file |
| `--command` | `reproduce-report` | Command to execute |
| `--repetitions` | 3 | Number of repetitions for determinism validation |
