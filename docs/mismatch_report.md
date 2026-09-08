# Mismatch Report

> 📖 **New here?** See the [Glossary](glossary.md) for terms like
> *cumulant*, *tolerance*.

## What is a "mismatch"?

A mismatch is a place where Convexfolio doesn't quite match the math
paper, or where you'd need to extend the package to handle real-world
data.

This page lists every known mismatch. None are critical — they're
disclosed for transparency.

---

## Known mismatches

### 1. Synthetic data vs real market data

**Severity**: Low (Design Decision)

**Description**: The `Reproduce` pipeline uses synthetic data when
called without `experiment.inputs`. The package ships with a
deterministic seed-driven synthetic generator so the demo is
self-contained; there's no built-in feed from a real-options data
source.

**Impact**: Results from the synthetic-data path of `Reproduce` don't
represent real market conditions.

**Resolution**: For real-world use, supply your own
`PortfolioInputs` (or write a small adapter that builds one from your
market data) and call `Reproduce(experiment)()` with `experiment.inputs`
populated. The solver classes don't care where the inputs come from.

### 2. Numerical optimisation tolerance

**Severity**: Low

**Description**: Numerical solvers inherit tolerances from SciPy.
`CFVaR3Numerical` passes `maxiter=1000, ftol=1e-9` for headroom.

**Impact**: Different CPUs or NumPy builds may give results that
agree to 10⁻⁶ but not 10⁻¹⁵. This is normal floating-point behaviour,
not a bug.

**Resolution**: If you need tighter reproducibility, set your own
solver options or run in a pinned container.

### 3. CFVaR3 third cumulant

**Severity**: Low (Demo Only)

**Description**: The demo pipeline uses
`synthetic_kappa3_from_seed(seed, u, v, Q)` — a deterministic,
weight-dependent third-cumulance callback driven by the experiment
seed. Real applications would supply an actual third cumulance
(e.g. via `Cumulant(...).value`) for their data.

**Impact**: CFVaR3 results from the demo use the seed-derived
synthetic kappa3; for real data, swap in a `Cumulant`-based callback
to use the paper's full formula.

**Resolution**: When using `CFVaR3Numerical`, pass a real
`kappa3_callback` to `CFVaR3Objective` (e.g. `lambda w: Cumulant(...).value`).

---

## Potential future mismatches

Things we *might* add but haven't yet.

### 1. Parallel processing

**Status**: Not Implemented

**Description**: Large portfolio optimisation could benefit from
parallel computation across instruments.

**Impact**: Performance for very large portfolios. For typical
5–50 instrument problems, single-threaded is fine.

### 2. GPU acceleration

**Status**: Not Implemented

**Description**: Matrix operations (especially `Linearize` and
`Reconstruct`) could be accelerated on a GPU.

**Impact**: Compute time for very large portfolios. Currently the
package uses NumPy, which is already fast for CPU.

### 3. Real-market data ingestion

**Status**: Not Implemented

**Description**: A built-in data loader for CSV / Parquet /
market-data APIs.

**Impact**: Users currently wire their own data pipeline.

---

## Reporting new mismatches

If you find a place where the code doesn't match the paper, or you
hit a real-world situation the package doesn't handle, please open
a GitHub issue with:

- **Description** — what the mismatch is.
- **Steps to reproduce** — minimal code or commands.
- **Expected vs actual behaviour** — what you expected, what
  happened.
- **Impact assessment** — how serious is this for your use case.

For security issues, see [SECURITY.md](../SECURITY.md) instead of
opening a public issue.

---

## Where to look next

- **[Glossary](glossary.md)** — Plain-English definitions.
- **[Fidelity Report](fidelity_report.md)** — Algorithm-by-algorithm
  mapping from paper to code.
- **[Research Determination Notes](research_determination.md)** —
  Which quantities are well-defined vs assumed.
- **[Architecture](architecture.md)** — How the package fits together.
