# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
