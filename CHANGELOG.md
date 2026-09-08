---
layout: page
title: "Changelog"
---
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-09-08

First production-stable release. The public API established in
0.3.0 is unchanged; the only deltas are project metadata, CLI
ergonomics, and operational polish.

### Added
- `convexfolio --version` flag, powered by `importlib.metadata.version`.
- `.github/CODEOWNERS` mapping all paths to `sachncs@gmail.com`.
- Friendly one-line error messages for missing `--config` paths,
  invalid JSON / YAML, and out-of-range `alpha` (no raw tracebacks
  on bad CLI input).

### Changed
- Version bumped to `1.0.0`.
- Trove classifier restored to `Development Status :: 5 - Production/Stable`.
- Package description drops the "research-preview" qualifier
  while keeping the explicit "not investment advice" disclaimer.
- `CITATION.cff` abstract drops the "research-preview" qualifier
  while keeping the "not investment advice" line; release date
  bumped to 2026-09-08.
- `Reproduce.__call__` now honours `Experiment.inputs` instead of
  discarding it; if `inputs` is `None` the synthetic 5-instrument
  path is still used and the result carries an explicit
  `uncertainty.ASSUMPTION` annotation.
- CFVaR3 solver receives a real, weight-dependent third-cumulance
  callback (`synthetic_kappa3_from_seed`) instead of a constant
  zero, so the third-order correction is genuinely active in the
  shipped pipeline.
- `CFVaR2nd` validation of `SyntheticPortfolio.degrees_of_freedom`
  tightened to reject `nu <= 2.0` (the lower bound for finite
  Student-t variance), eliminating a divide-by-zero in the (1.0, 2.0]
  range that previously slipped past the `> 1.0` check.

### Fixed
- `SyntheticPortfolio` no longer divides by zero when
  `1.0 < degrees_of_freedom <= 2.0`.
- `Reproduce.__call__` no longer overwrites user-supplied inputs
  with synthetic data.
- `Backtest.run_backtest` rebalance fallback uses a budget-feasible
  starting point and respects the previous feasible weights when
  the solver fails (`tolerate_solver_failure=True` opt-in).
- `CHANGELOG.md [0.3.0]` no longer has a duplicated `### Changed`
  section.
- `convexfolio/__init__.py __all__` is now sorted alphabetically and
  the `Report` entry is correctly indented.
- Architecture diagram in `docs/architecture.md` no longer contains a
  U+FFFD replacement character; references to deleted
  `pipeline.py` / `determinism.py` modules removed.
- `apis` referenced in docs (`load`, `reproduce`, `validate`,
  `check`, `run_and_save`) replaced with the actual CapWords
  public classes (`Load`, `Reproduce`, `Validate`,
  `Report.from_reproduce`).
- README quick-start example shows the actual solver output
  (`[1.0591133, 0.91133005]`) instead of a fabricated
  `[0.65, 0.95]`.
- `mypy` configuration switched to `strict = true`.
- All closure factories (`budget.fun`, `inequality.fun`,
  `variance_at` in `Reconstruct.__init__`) hoisted to module level
  with Google-style docstrings.
- `isinstance(...)` removed from production code; `assert`
  preconditions replaced with typed `raise` statements.

### Removed
- `long_only_bounds` and `position_limits_bounds` thin wrappers
  (callers use `bounds(...)` directly).
- `_ITERS`, `_BENCHMARK_PLUGIN`, `_wall_clock_run`, `_has_plugin`,
  `_run` underscored module-level helpers in `benchmarks/test_benchmarks.py`.
- The `bench` optional-dependency extra (`pytest-benchmark` is now
  a required runtime dependency).

## [0.3.0] - 2026-08-22

### Changed
- **BREAKING**: Package renamed from `options` to `convexfolio`. The
  Python import path is now `convexfolio`, the CLI command is now
  `convexfolio`, and the GitHub repository is `sachncs/convexfolio`.
  No compatibility shim is provided — `import options` and the `options`
  CLI command no longer work.
- **BREAKING**: Dropped support for Python 3.10 and Python 3.11.
  Minimum supported version is now Python 3.12.
- **BREAKING**: Tightened all dependency pins from `>=X.Y` to exact
  `==X.Y.Z`. Downstream users must now match pinned versions.
- **BREAKING**: Removed the `Risk` class facade from `convexfolio.math`;
  callers should compose `CFVaR2nd` and `CFVaR3rd` directly.
- **BREAKING**: Removed the Sphinx documentation build pipeline
  (`docs/conf.py`, `docs/*.rst`, `docs/_build`, `docs/_static`). All
  documentation now lives in Markdown files under `docs/`.
- Upgraded runtime dependencies: `numpy==2.5.2`, `scipy==1.18.0`,
  `pyyaml==6.0.3`.
- Upgraded dev dependencies: `pytest==9.1.1`, `mypy==2.3.1`,
  `ruff==0.16.4`.
- Upgraded bench dependencies: `pytest-benchmark==5.2.3`,
  `py-cpuinfo==9.0.0` (new required transitive dep).
- Upgraded build-system dependencies: `setuptools==84.0.0`,
  `wheel==0.48.0`.

### Fixed
- `CFVaR3Numerical` now passes `maxiter=1000, ftol=1e-9` to SLSQP so
  the solver converges on the synthetic `reproduce()` input across
  platforms (Python 3.12 vs 3.13).
- `reproduce()` now starts `CFVaR3Numerical` from the feasible point
  `cost_vector / (cost_vector @ cost_vector)` instead of
  `np.ones(n) / np.sum(cost_vector)`, eliminating wasted SLSQP
  iterations satisfying the budget constraint.

## [0.2.1] - 2026-05-09

### Added
- CI workflow with lint, type-check, tests, build, and wheel smoke test.
- Deterministic validation capability for reproducibility checks.
- Research determination notes for `c`, `h`, `q`, and `epsilon_star`.

### Changed
- CFVaR2 closed-form solver now computes `epsilon_star` from Appendix-B derivation.
- Reproduction math now uses variance-consistent `Q` reconstruction for exact quadratic behavior.

## [0.2.0] - 2026-05-09

### Added
- Production package rename to `oop`.
- Public API, CLI, config, logging, pipeline, tests, and docs.

### Changed
- Migrated to production-ready package structure.

## [0.0.1] - 2026-05-09

### Added
- Initial release with core optimization algorithms.
- Variance minimization solver.
- CFVaR2 closed-form solver.
- CFVaR3 numerical solver.

[Unreleased]: https://github.com/sachncs/convexfolio/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/sachncs/convexfolio/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/sachncs/convexfolio/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/sachncs/convexfolio/compare/v0.0.1...v0.2.0
[0.0.1]: https://github.com/sachncs/convexfolio/releases/tag/v0.0.1
