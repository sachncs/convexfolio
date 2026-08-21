# Fidelity Report

## Overview

This document describes the fidelity of the implementation to the
reference paper [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2).

## Paper Fidelity

### Variance Minimization (Section 2.1)

**Status**: Fully Implemented

The minimum variance portfolio optimization under budget constraint is
implemented as:

```
minimize    0.5 x^T Q x
subject to  x^T v = 1
```

**Implementation**: `Minimize(Variance(Q), v).value` in
`convexfolio/math.py`. Closed-form solution: `x* = Q⁻¹v / (v� Q⁻¹ v)`.

### CFVaR2 Closed-Form (Section 4.2)

**Status**: Fully Implemented

The closed-form solution for CFVaR2 optimization is implemented
analytically via Appendix-B epsilon-star derivation and the QP with
dual variables.

**Implementation**: `CFVaR2Closed(Q, u, v, alpha).value` in
`convexfolio/math.py`. Uses `OptimalEpsilon` for the Lagrange multiplier.

### CFVaR3 Numerical (Section 4.3)

**Status**: Fully Implemented

Third-order risk measure optimization via numerical methods (SLSQP).

**Implementation**: `CFVaR3Numerical(v, x0, objective).value` with
`CFVaR3Objective(alpha, u, Q, κ₃_callback)` in `convexfolio/math.py`.

### Risk evaluation

**Status**: Fully Implemented

- `CFVaR2nd(alpha, u, Q, x).value` — second-order CFVaR at weights `x`.
- `CFVaR3rd(alpha, u, Q, x, κ₃).value` — third-order CFVaR with cumulance
  correction.

### Section 2.4 — determined quantities

**Status**: Fully Implemented

- `c`: `Compute(degrees_of_freedom).value` (skew-t coefficient).
- `h`: `Linear(covariance, skewness).value` (linear bias vector).
- `q`: `Curvature(third_derivative, h).values` (curvature vector).
- `Q` reconstruction: `Reconstruct(...).value` (variance-consistent
  recovery of the symmetric precision matrix).
- `u`, `Q` linearised: `Linearize(...).dual_residual`,
  `Linearize(...).precision_matrix`.

## Parameter Definitions

### `c` (Eq. 3)

**Status**: Implemented

The scalar `c` from the moment expansion is computed in `Compute`
(`convexfolio/math.py`).

### `h` (Eq. 3)

**Status**: Implemented

The vector `h` from the moment expansion is computed in `Linear`
(`convexfolio/math.py`).

### `q` (Eq. 3)

**Status**: Implemented

The curvature vector `q` is computed in `Curvature`
(`convexfolio/math.py`).

### `epsilon_star` (Appendix B)

**Status**: Implemented

The optimal `epsilon_star` scalar is computed from the Appendix B
derivation in `OptimalEpsilon` (`convexfolio/math.py`). Closed-form
roots preferred; bounded numerical fallback if root conditions fail.

## Mismatches and Caveats

### Synthetic Data

**Status**: ASSUMPTION

The pipeline in `reproduce()` uses synthetic data for demonstration.
Real-market replication requires data-specific integration.

### Numerical Precision

**Status**: ASSUMPTION

Numerical optimization may have slight variations across platforms due
to floating-point arithmetic. `CFVaR3Numerical` passes
`maxiter=1000, ftol=1e-9` to SLSQP for headroom.

### Estimator Parity with R `sn`

**Status**: NOT DETERMINED

Some statistical estimators may differ from R's `sn` package
implementations.

## Testing Coverage

All implemented algorithms are covered by unit tests in `tests/`:

- `test_optimization.py` — Solver correctness
  (`Minimize`, `CFVaR2Closed`, `CFVaR3Numerical`).
- `test_risk.py` — Risk measure calculations (`CFVaR2nd`, `CFVaR3rd`,
  `Quadratic`, `shapes`).
- `test_config.py` — Configuration validation (`load`, `validate`).
- `test_determinism.py` — Reproducibility verification (`check`).
- `test_determined_quantities.py` — Section 2.4 parameter computation
  (`Compute`, `Linear`, `Reconstruct`, `PortfolioVariance`).
