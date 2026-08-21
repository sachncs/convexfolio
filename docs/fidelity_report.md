# Fidelity Report

> 📖 **New here?** See the [Glossary](glossary.md) for terms like
> *variance*, *CFVaR*, *precision matrix*.

## What does "fidelity" mean?

"Fidelity" is a fancy word for **fidelity** — does this code do what
the math paper says?

This page tracks, algorithm by algorithm, whether the Convexfolio
code is a faithful implementation of
[arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2).

For each piece of math in the paper, we list:

- **What the paper says** (in plain English).
- **What the code does** (which class/function, in which file).
- **Status**: Implemented / Partial / Not done.

If you want to know "can I trust this code for X?", this is the page.

---

## Paper fidelity

### Variance Minimisation (Section 2.1)

**Status**: Fully Implemented

The paper says: find the weights `x` that minimise `0.5 xᵀQx`
subject to `xᵀv = 1` (the budget constraint). Convexfolio solves
this with an exact formula.

| | |
|---|---|
| **Plain English** | Given the precision matrix `Q` (how risky each option is) and the cost vector `v` (option prices), find the weights that minimise variance while spending exactly $1. |
| **Class** | `Minimize(Variance(Q), v)` |
| **Where** | `convexfolio/math.py` |
| **Method** | Closed-form: `x* = Q⁻¹v / (vᵀQ⁻¹v)` |

### CFVaR2 Closed-Form (Section 4.2)

**Status**: Fully Implemented

The paper says: find the weights that minimise CFVaR2 (a sharper risk
measure than variance), using an exact formula based on the
epsilon-star derivation in Appendix B.

| | |
|---|---|
| **Plain English** | Solve the same kind of problem, but use a risk measure that's better at catching tail losses. |
| **Class** | `CFVaR2Closed(Q, u, v, alpha)` |
| **Where** | `convexfolio/math.py` |
| **Method** | Closed-form via `OptimalEpsilon` for the Lagrange multiplier. |

### CFVaR3 Numerical (Section 4.3)

**Status**: Fully Implemented

The paper says: solve for weights using a third-order approximation
of CFVaR. Convexfolio uses SciPy's SLSQP optimiser under the hood.

| | |
|---|---|
| **Plain English** | Same goal as CFVaR2, but using a more accurate risk approximation. Slower (no closed form exists) but closer to the paper. |
| **Class** | `CFVaR3Numerical(v, x0, objective)` with `CFVaR3Objective(alpha, u, Q, κ₃_callback)` |
| **Where** | `convexfolio/math.py` |
| **Method** | SLSQP, with `maxiter=1000, ftol=1e-9` for headroom. |

### Risk evaluation

**Status**: Fully Implemented

For any candidate weight vector `x`, compute the actual risk number
it would produce.

| | |
|---|---|
| **Plain English** | Given a portfolio, what does its risk number actually look like? |
| **Classes** | `CFVaR2nd(alpha, u, Q, x)` and `CFVaR3rd(alpha, u, Q, x, κ₃)` |
| **Where** | `convexfolio/math.py` |

### Section 2.4 — determined quantities

**Status**: Fully Implemented

The paper builds a precision matrix `Q` from raw option Greeks data.
Convexfolio provides classes for every intermediate quantity.

| Paper quantity | Convexfolio class |
|---|---|
| `c` (skew-t coefficient) | `Compute(degrees_of_freedom).value` |
| `h` (linear bias vector) | `Linear(covariance, skewness).value` |
| `q` (curvature vector) | `Curvature(third_derivative, h).values` |
| Bilinear / cross matrices | `Bilinear(...).matrix`, `Cross(...).matrix` |
| `Q` reconstruction | `Reconstruct(...).value` |
| Linearised `u`, `Q` | `Linearize(...).dual_residual`, `Linearize(...).precision_matrix` |

---

## Parameter Definitions

### `c` (Eq. 3)

**Status**: Implemented

The skew-t coefficient. Computed by `Compute(degrees_of_freedom)` in
`convexfolio/math.py`.

### `h` (Eq. 3)

**Status**: Implemented

The linear bias vector. Computed by `Linear(covariance, skewness)`
in `convexfolio/math.py`.

### `q` (Eq. 3)

**Status**: Implemented

The curvature vector. Computed by `Curvature(third_derivative, h)`
in `convexfolio/math.py`.

### `epsilon_star` (Appendix B)

**Status**: Implemented

The optimal Lagrange multiplier. Computed by `OptimalEpsilon(...)`
in `convexfolio/math.py`. Closed-form roots preferred; bounded
numerical fallback if roots fail.

---

## Mismatches and Caveats

### Synthetic Data

**Status**: ASSUMPTION

The pipeline in `reproduce()` uses synthetic data for demonstration.
Real-market replication requires data-specific integration. See
[Mismatch Report](mismatch_report.md).

### Numerical Precision

**Status**: ASSUMPTION

Numerical optimisation may give slightly different results across
platforms due to floating-point arithmetic. `CFVaR3Numerical`
passes `maxiter=1000, ftol=1e-9` to SLSQP for headroom.

### Estimator Parity with R `sn`

**Status**: NOT DETERMINED

Some statistical estimators may differ from R's `sn` package
implementations. We haven't done a head-to-head comparison.

---

## Testing coverage

Every algorithm above has a unit test. ([Glossary: pytest](glossary.md))

| File | What it tests |
|---|---|
| `tests/test_optimization.py` | `Minimize`, `CFVaR2Closed`, `CFVaR3Numerical` correctness. |
| `tests/test_risk.py` | `CFVaR2nd`, `CFVaR3rd`, `Quadratic`, `shapes`. |
| `tests/test_config.py` | `load`, `validate`. |
| `tests/test_determinism.py` | `check` (reproducibility). |
| `tests/test_determined_quantities.py` | `Compute`, `Linear`, `Reconstruct`, `PortfolioVariance` (Section 2.4). |

Run them all with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

---

## Where to look next

- **[Glossary](glossary.md)** — Plain-English definitions.
- **[Mismatch Report](mismatch_report.md)** — Detailed list of known
  differences between code and paper.
- **[Research Determination Notes](research_determination.md)** —
  Which quantities are well-defined vs assumed.
- **[Architecture](architecture.md)** — How the package fits together.
