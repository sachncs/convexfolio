# Research Determination Notes

> 📖 **New here?** See the [Glossary](glossary.md) for terms like
> *variance*, *cumulant*, *alpha*.

## What is "determination status"?

Some math quantities in the paper are nailed down — there's only one
sensible way to compute them. Others depend on assumptions, are still
being worked out, or are simply unknown.

This page tracks, quantity by quantity, **which is which**. So if you
need to know "is `c` in the package trustworthy, or did the author
just guess?", this page tells you.

---

## Status legend

Each quantity gets one of these four labels:

| Label | What it means |
|---|---|
| **DETERMINED** | Verified and implemented exactly as the paper specifies. |
| **ASSUMPTION** | Implemented based on a reasonable interpretation; not nailed down by the paper. |
| **NOT DETERMINED** | The paper doesn't fully resolve this. |
| **UNKNOWN** | We don't know the status yet. |

---

## Parameters

### `c` — skew-t coefficient

**Status**: DETERMINED

A scalar computed from the skew-t distribution's degrees of freedom.

| | |
|---|---|
| **Source** | Section 2.4 of the paper. |
| **Class** | `Compute(degrees_of_freedom).value` |
| **Where** | `convexfolio/math.py` |

### `h` — linear bias vector

**Status**: DETERMINED

A vector computed from the covariance matrix and the skewness vector.

| | |
|---|---|
| **Source** | Section 2.4. |
| **Class** | `Linear(covariance, skewness).value` |
| **Where** | `convexfolio/math.py` |

### `q` — curvature vector

**Status**: DETERMINED

A vector capturing how the second derivative of each option
contributes to the portfolio.

| | |
|---|---|
| **Source** | Section 2.4. |
| **Class** | `Curvature(third_derivative, h).values` |
| **Where** | `convexfolio/math.py` |

### `H` — bilinear expansion matrix

**Status**: DETERMINED

| | |
|---|---|
| **Source** | Section 2.4. |
| **Class** | `Bilinear(...).matrix` |
| **Where** | `convexfolio/math.py` |

### `E` — cross-term matrix

**Status**: DETERMINED

The transpose of `H`. ([Glossary: transpose](glossary.md))

| | |
|---|---|
| **Source** | Section 2.4. |
| **Class** | `Cross(...).matrix` |
| **Where** | `convexfolio/math.py` |

### `epsilon_star` (ε*) — optimal Lagrange multiplier

**Status**: DETERMINED

The optimal Lagrange multiplier that makes the CFVaR2 closed-form
solution work.

| | |
|---|---|
| **Source** | Appendix B derivation. |
| **Class** | `OptimalEpsilon(alpha, u, v, Q).value` |
| **Where** | `convexfolio/math.py` |
| **Note** | Closed-form roots preferred; bounded numerical fallback if roots fail. |

### `Q` reconstruction

**Status**: DETERMINED

Recovers the symmetric precision matrix from raw option Greeks data.

| | |
|---|---|
| **Source** | Section 2.4 (variance-consistent derivation). |
| **Class** | `Reconstruct(...).value` |
| **Where** | `convexfolio/math.py` |
| **Verified by** | `tests/test_determined_quantities.py::test_reconstructed_q_matches_direct_variance_formula` |

---

## Algorithm parameters

### `alpha` — risk confidence level

**Status**: DETERMINED

| | |
|---|---|
| **Source** | Section 4.1. |
| **Constraint** | `0 < alpha < 0.5` (enforced by `convexfolio.config.validate`). |
| **Default** | `0.05` (set by `Optimization.alpha`). |

Smaller alpha means the optimiser is more cautious about rare-but-bad
outcomes.

### `nu` — degrees of freedom

**Status**: ASSUMPTION

The skew-t distribution's degrees-of-freedom parameter. The paper
constrains it loosely; Convexfolio assumes `nu > 6` by default.

| | |
|---|---|
| **Source** | Section 4.2. |
| **Constraint** | `nu > 6` (configurable via `enforce_nu_greater_than_six`). |
| **Why `nu > 6`** | The skew-t coefficient `c` requires `nu > 1` to be finite; `nu > 6` is the paper's stricter bound. |
| **Toggle** | `Optimization.enforce_nu_greater_than_six` (default `True`). |

### `method` — which solver to run

**Status**: DETERMINED

| | |
|---|---|
| **Source** | Section 4. |
| **Options** | `all`, `variance`, `cfvar2`, `cfvar3`. |
| **Where** | `Optimization.method`. |

---

## Implementation notes

### Variance-consistent `Q` reconstruction

**Status**: DETERMINED

The `Q` matrix reconstruction uses a variance-consistent formulation
so the quadratic form `0.5 xᵀQx` matches the direct portfolio
variance computation to ~10�⁷ precision.

Verified by `tests/test_determined_quantities.py::test_reconstructed_q_matches_direct_variance_formula`.

### Deterministic seed control

**Status**: DETERMINED

All random operations go through `numpy.random.default_rng(seed)`,
so the same `Runtime.seed` always produces the same random sequence.

This guarantees **deterministic execution** — same inputs always
produce same outputs. The `validate-determinism` CLI command verifies
this end-to-end.

---

## Open questions

Things we haven't figured out yet. Not blockers, but worth noting.

1. **Optimal solver tolerances for different portfolio sizes.** The
   `ftol=1e-9` setting in `CFVaR3Numerical` is conservative; smaller
   portfolios might not need it, larger ones might.
2. **Parallelisation strategy for large-scale problems.** The
   determinism check uses a process pool when `repetitions ≥
   OPTIONS_PARALLEL_THRESHOLD` (default 4), but the core solvers are
   single-threaded.
3. **GPU acceleration feasibility.** Worth investigating for very
   large portfolios, but not implemented.

---

## References

- [arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2) — Main
  paper.
- [R `sn` package](https://CRAN.R-project.org/package=sn) —
  Reference implementation for statistical estimators. Parity has not
  been verified.

---

## Where to look next

- **[Glossary](glossary.md)** — Plain-English definitions.
- **[Fidelity Report](fidelity_report.md)** — Algorithm-by-algorithm
  mapping from paper to code.
- **[Mismatch Report](mismatch_report.md)** — Known places where the
  code and paper diverge.
- **[Architecture](architecture.md)** — How the package fits
  together.
