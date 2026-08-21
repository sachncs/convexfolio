# Research Determination Notes

## Overview

This document tracks the determination status of various parameters and
quantities from the paper
[arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2).

## Status Legend

- **DETERMINED** — Quantity has been verified and implemented.
- **ASSUMPTION** — Implementation based on reasonable assumption.
- **NOT DETERMINED** — Quantity not fully resolved.
- **UNKNOWN** — Status unknown.

## Parameters

### `c` (Scalar from Eq. 3)

**Status**: DETERMINED

**Source**: Section 2.4, extracted from HTML.

**Implementation**: `Compute(degrees_of_freedom).value` in
`convexfolio/math.py`.

### `h` (Vector from Eq. 3)

**Status**: DETERMINED

**Source**: Section 2.4, extracted from HTML.

**Implementation**: `Linear(covariance, skewness).value` in
`convexfolio/math.py`.

### `q` (Quadratic Form from Eq. 3)

**Status**: DETERMINED

**Source**: Section 2.4, extracted from HTML.

**Implementation**: `Curvature(third_derivative, h).values` in
`convexfolio/math.py`.

### `H` (Matrix from Eq. 3)

**Status**: DETERMINED

**Source**: Section 2.4, extracted from HTML.

**Implementation**: `Bilinear(...).matrix` in `convexfolio/math.py`.

### `E` (Matrix from Eq. 3)

**Status**: DETERMINED

**Source**: Section 2.4, extracted from HTML.

**Implementation**: `Cross(...).matrix` (transpose of `Bilinear`).

### `epsilon_star` (Appendix B)

**Status**: DETERMINED

**Source**: Appendix B derivation.

**Implementation**: `OptimalEpsilon(alpha, u, v, Q).value` in
`convexfolio/math.py`.

### `Q` reconstruction

**Status**: DETERMINED

**Source**: Section 2.4 (variance-consistent derivation).

**Implementation**: `Reconstruct(...).value` in `convexfolio/math.py`.

## Algorithm Parameters

### `alpha` (Risk Parameter)

**Status**: DETERMINED

**Source**: Section 4.1.

**Constraint**: `0 < alpha < 0.5`. Enforced by `convexfolio.config.validate`.

**Default**: `0.05` (`Optimization.alpha`).

### `nu` (Degrees of Freedom)

**Status**: ASSUMPTION

**Source**: Section 4.2.

**Constraint**: `nu > 6` (configurable).

**Implementation**: Enforced via the `enforce_nu_greater_than_six`
field of `Optimization`. The skew-t coefficient `c` requires `nu > 1`
to be finite; `nu > 6` is the paper's stricter bound.

### `method` (Optimization Method)

**Status**: DETERMINED

**Source**: Section 4.

**Options**: `all`, `variance`, `cfvar2`, `cfvar3` (selector on
`Optimization.method`).

## Implementation Notes

### Variance-Consistent Q Reconstruction

**Status**: DETERMINED

The `Q` matrix reconstruction uses variance-consistent formulation
(`Reconstruct`) for exact quadratic behavior. Verified in
`tests/test_determined_quantities.py::test_reconstructed_q_matches_direct_variance_formula`.

### Deterministic Seed Control

**Status**: DETERMINED

All random operations are seeded for reproducibility via
`np.random.default_rng(seed)`, where `seed` comes from
`Runtime.seed` (default `7`).

## Open Questions

1. Optimal solver tolerances for different portfolio sizes.
2. Parallelization strategy for large-scale problems.
3. GPU acceleration feasibility.

## References

- [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2) — Main paper.
- [R `sn` package](https://CRAN.R-project.org/package=sn) — Reference
  implementation for statistical estimators.
