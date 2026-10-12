# Convexfolio v2: production-readiness, architecture, testing, and site redesign

## 1. Objective and constraints

### Objective

Deliver a breaking v2 release that is:

- Numerically validated and failure-transparent.
- Testable on a clean machine.
- Structured around explicit OOP interfaces and polymorphism.
- Consistent with Google Python style.
- Resilient to malformed inputs, infeasible constraints, solver failures, and missing data.
- Supported by accurate documentation.
- Presented through an accessible, responsive, technically credible website.

### Non-negotiable constraints

- No live trading, brokerage, authentication, or external account integrations.
- No silent solver fallback.
- No unvalidated numerical result may be returned as successful.
- No undocumented public API.
- No claim of “production ready,” “exact,” “lowest risk,” or “byte-identical” without a corresponding invariant and automated test.
- No mutation of caller-owned arrays or configuration dictionaries.
- No new dependency may be added without justification, license review, and CI coverage.
- v2 may break the v1 API, but migration guidance is required.
- Support Python `>=3.12,<3.15`; Python 3.14 compatibility was verified locally before adding it to CI.
- Site remains static and GitHub Pages-hosted.
- Astro is the only documentation/site source of truth. No Jekyll files,
  generated documentation copies, or parallel page systems may remain.
- The implementation must not be considered complete until local and CI checks pass from a clean environment.

### Execution status — 2026-10-12

Completed in the current working tree:

- Reproducible Python 3.12–3.14 environment, pinned development tooling,
  CI matrix, and build smoke test.
- `Vector` and `Matrix` validated read-only value objects with explicit
  `.copy()` and `.validate()` methods; no semi-private application helpers
  remain in the public package surface.
- Configuration, input, price, matrix, alpha, constraint, and numerical
  validation with typed domain errors.
- ABC-based polymorphic risk, constraint, and optimizer contracts with
  structured diagnostics and SLSQP failure reporting.
- Stable linear solves, corrected sector/leverage constraints, holdings-based
  marked-to-market backtests, and expanded CLI/domain tests.
- Optional dependency groups for plotting, Hugging Face ingestion, and
  benchmarks; core package installation no longer pulls them in.
- Accessible site interaction updates, a restrained editorial green/cream
  visual system, truthful homepage claims, and a dependency-free site
  invariant check.
- Jekyll has been removed. Astro now owns the homepage, documentation shell,
  Markdown content collection, static build, and GitHub Pages artifact.
- Documentation tone was revised toward direct technical language: claims are
  scoped, limitations are visible, and the homepage leads with inspectability
  rather than marketing language.
- Report output has a `2.0` schema version and the process-parallel report path
  is covered by tests.
- Local quality verification now passes at 196 tests, 92.55% combined
  coverage, 94.50% package coverage, package/branch coverage thresholds, Ruff,
  Mypy, wheel installation, and CLI smoke test.
- The current CI-equivalent Python 3.13 run passes 189 tests with 92.56%
  total coverage, 94.51% package coverage, and the critical branch checks.
- Astro type-checks and builds 18 routes. A live preview audit verified the
  homepage and documentation navigation, then caught and fixed the GitHub
  Pages base-path separator bug.
- Astro is pinned to `7.3.8`; `npm audit --audit-level=high` reports zero
  vulnerabilities for the documentation toolchain.
- The homepage includes an accessible, no-network two-instrument solver
  example with a meaningful no-JavaScript fallback.
- Chrome rendered the homepage at 320px, 768px, and 1440px viewport widths;
  the mobile pass found and fixed content overflow, and all three renders now
  have bounded layouts with responsive controls. The preview produced no
  page-level console errors.
- Lighthouse accessibility is 100/100 on the local Astro preview, including a
  passing WCAG color-contrast audit.
- The marketing homepage has been visually redesigned around inspectability:
  an editorial hero, truthful local solver demo, signal strip, principles,
  workflow, scope notice, and responsive CTA hierarchy.
- The logo and favicon now use one custom geometric mark: an open C, a convex
  arc, and a single data-point dot in the site palette; the old glossy blue
  gradient mark has been removed.
- The architecture page now renders a responsive semantic flow graph rather
  than a fenced ASCII diagram. The graph exposes the input/configuration,
  domain-contract, polymorphic strategy, and diagnostics/report boundaries,
  with an ordered reading fallback.
- Release CI now runs the Python/site quality gate; the container workflow
  builds and smoke-tests the CLI image; package metadata no longer claims
  Production/Stable.
- Python 3.13 was reproduced locally with the documented development install:
  189 tests passed, with Ruff, Mypy, coverage, and release metadata checks
  passing.
- The full CI command sequence was rerun from the current checkout: 189 tests
  passed, 7 benchmark cases passed, documentation checks compiled 34 Python
  blocks, the Astro dependency install was clean, and the Astro build emitted
  no diagnostics or unsupported syntax-highlighting warnings.
- A freshly built `convexfolio-2.0.0-py3-none-any.whl` installed into a clean
  Python 3.13 virtual environment and the installed CLI emitted a parseable
  report with the expected `config`, `inputs`, `outputs`, and `uncertainty`
  sections.
- All 34 fenced Python documentation blocks compile, the canonical
  getting-started example and CSV/constraints/backtesting tutorial workflows
  execute in the test suite, and the process-pool
  worker is exposed as the documented `reproduce_once` function rather than
  a semi-private underscored helper.
- Package metadata, citation metadata, README installation instructions, and
  the changelog identify the locally verified breaking release as `2.0.0`; an
  annotated `v2.0.0` tag points at the published release snapshot
  `326b226`.
- The previous stable baseline is recoverable locally through an annotated
  `v1.0.0` tag at commit `8f266d0`, which carries the matching historical
  `1.0.0` metadata and changelog.

Hosted completion evidence — 2026-10-12:

- [CI run 38240361904](https://github.com/sachncs/convexfolio/actions/runs/38240361904)
  passed on `326b226` across the site, build, Python 3.12, 3.13, and 3.14
  jobs. The follow-up documentation-only push also passed in [CI run
  38240647622](https://github.com/sachncs/convexfolio/actions/runs/38240647622).
- [Release run 38240362035](https://github.com/sachncs/convexfolio/actions/runs/38240362035)
  passed and published the immutable `v2.0.0` release with both wheel and
  source archive assets.
- [Pages run 38240361920](https://github.com/sachncs/convexfolio/actions/runs/38240361920)
  passed for `326b226`; the follow-up Pages run
  `38240647551` also passed after the rollback documentation update. The live
  homepage, architecture graph, and release/rollback documentation routes
  were fetched successfully from `https://sachncs.github.io/convexfolio/`.
- Rollback evidence was exercised in a disposable clone: `v1.0.0` resolves to
  the prior stable tag, reports package version `1.0.0`, and remains an
  ancestor of `v2.0.0`. The release guide now documents separate package and
  Pages recovery procedures without force-moving published tags.

The plan gates are complete. Remaining GitHub annotations are non-failing
platform notices about Node.js 20 action runtimes and the future Ubuntu image
migration; they do not fail any quality gate.

## 2. Original issue inventory

This is the complete audit baseline captured before implementation. The
disposition below prevents resolved findings from being mistaken for current
defects.

### Environment and release process

- The repository previously had no reproducible local development environment
  or documented quality baseline.
- `pyproject.toml` advertises Python `>=3.12`, while CI tests only 3.12 and 3.13.
- Production dependencies include development/benchmark packages.
- Release workflow builds and publishes without running the full quality gate first.
- GitHub Actions are referenced by mutable major tags rather than reviewed immutable references.
- Docker workflow lacks explicit runtime hardening and a meaningful application smoke test.
- No enforced coverage threshold exists.
- No documentation, link, accessibility, or visual regression checks exist.

### Numerical and domain correctness

- Raw matrix inversions are used in optimization paths.
- Matrix symmetry, positive definiteness, finiteness, and conditioning are not centrally validated.
- Alpha, degrees of freedom, price, and portfolio input validation is incomplete.
- Solver results are not consistently checked for finite values, residuals, feasibility, or objective validity.
- SLSQP diagnostics are reduced to success/failure text.
- `sector_caps_inequalities()` creates coefficient vectors using sector count rather than instrument count.
- `leverage_cap_inequality()` implements signed exposure despite documenting absolute leverage.
- Constraint builders do not consistently reject invalid bounds, dimensions, limits, or non-finite values.
- `CFVaR` calculations can divide by zero or operate on degenerate variance.
- `OptimalEpsilon` uses an arbitrary bounded fallback search radius.
- Frozen dataclasses contain mutable NumPy arrays, so configuration is not truly immutable.
- Determinism claims do not distinguish reproducibility from byte-identical floating-point output across platforms.

### Configuration and data ingestion

- Malformed YAML roots can produce unclear attribute errors.
- Unknown configuration keys are not reported cleanly.
- Configuration loading mutates parsed dictionaries.
- Portfolio vector and matrix dimensions are not validated at the configuration boundary.
- CSV readers do not consistently reject ragged rows, blank rows, duplicate headers, invalid timestamps, non-finite values, or invalid prices.
- Price-history loading does not validate timestamps against price-row counts.
- Hugging Face ingestion has limited retry, timeout, observability, and offline-test structure.
- Error types are not consistently domain-specific or actionable.

### Backtesting

- Portfolio value is not marked to market between rebalances.
- Holdings, weights, returns, and transaction costs are not represented as separate concepts.
- Failed-rebalance fallback can violate extra constraints.
- Price scaling can divide by zero.
- Backtest configuration validation is incomplete.
- Backtest outputs lack solver diagnostics, skipped-period information, and explicit failure policy.
- Drawdown and cost behavior are not covered across sufficient edge cases.

### Architecture and code quality

- `math.py`, `hf_data.py`, `cli.py`, and `utils.py` contain too many responsibilities.
- Most computation happens in constructors and is exposed through `.value`.
- There is no explicit solver, risk-measure, constraint, data-source, or backtest-engine interface.
- Polymorphism is intentionally rejected by current documentation.
- Semi-private naming is inconsistent and undocumented.
- Public exports and documentation are not fully aligned.
- Google-style conventions are incomplete and contradicted by repository guidance.
- Naming rules prohibit useful abstractions while allowing large orchestration modules.
- CLI, reporting, file I/O, numerical logic, and plotting are coupled.

### Tests

- Current suite is mostly unit-level and happy-path oriented.
- No coverage gate.
- No property-based tests.
- No independent numerical reference tests.
- No systematic failure-injection tests.
- No contract tests for all constraint types.
- No broad backtest accounting tests.
- No clean-install, wheel, documentation, or site smoke-test coverage.
- No browser-level regression suite for the site.

### Documentation and website

- Documentation previously conflicted with the requested OOP/polymorphic design.
- Documentation describes only three CLI commands while the implementation exposes more.
- Claims about exactness, determinism, and production readiness are insufficiently qualified.
- Examples are not automatically executed against the current API.
- Homepage is visually over-decorated and marketing-heavy for a research library.
- Palette has excessive mint/teal/glow usage and weak hierarchy.
- Mobile and desktop navigation were duplicated in the previous Jekyll shell.
- Focus-visible styling is not explicit.
- Mobile menu lacks complete focus management and Escape handling.
- Tabs lack complete ARIA relationships and keyboard semantics.
- Copy feedback lacks an accessible live region and meaningful failure state.
- Animated counters expose `0` before hydration.
- Typewriter behavior uses randomness despite determinism messaging.
- Automated source/link checks now exist; rendered contrast, overflow, and
  responsive checks remain release gates.

### Disposition

Resolved: dependency separation, Python 3.14 CI coverage, coverage gates,
validation boundaries, stable solves, solver diagnostics, constraint bugs,
backtest accounting, public OOP contracts, semi-private array helpers, report
schema versioning, documentation links, Jekyll removal, Astro migration,
homepage tone/claims, Docker build context, release quality gates, Astro
toolchain security, immutable GitHub Action references, matrix conditioning
validation, Hugging Face transient retries, and optional plotting test
isolation.

Still open or requiring stronger evidence: hosted-runner CI confirmation and
the release-event checks that cannot be performed without publishing v2.
These remain explicit release gates below.

## 3. Target architecture

### Package layers

Create explicit modules for:

- `domain`: immutable portfolio, market, constraint, and result models.
- `risk`: risk-measure interfaces and concrete variance/CFVaR implementations.
- `optimization`: optimizer interfaces, closed-form solvers, and numerical solvers.
- `constraints`: typed constraint objects and feasibility evaluation.
- `data`: validated data sources and parsers.
- `backtest`: holdings-based simulation engine.
- `application`: orchestration and report generation.
- `cli`: argument parsing and command adapters.
- `infrastructure`: logging, serialization, filesystem, and optional integrations.

### Required public interfaces

Define typed interfaces for:

- `RiskMeasure.evaluate(portfolio) -> RiskEvaluation`
- `Optimizer.solve(problem) -> OptimizationResult`
- `Constraint.residual(weights) -> float`
- `Constraint.check(weights, tolerance) -> ConstraintResult`
- `DataSource.iter_rows() -> Iterator[ValidatedRow]`
- `BacktestEngine.run() -> BacktestResult`

Every result must include status, diagnostics, warnings, objective value, feasibility, and relevant residuals.

### Numerical policy

Create one central tolerance/configuration policy containing:

- Budget tolerance: `1e-8`.
- Constraint tolerance: `1e-8`.
- Finite-value requirement.
- Matrix conditioning checks.
- Maximum solver iterations.
- Convergence policy.
- Deterministic initial-weight policy.

All solvers must use this policy and reject invalid results.

## 4. Implementation phases and gates

### Phase 0 — Reproducible baseline

Deliver:

- Development bootstrap instructions or script.
- Supported Python version policy.
- Clean dependency groups.
- Baseline test, lint, type, build, and documentation commands.
- Initial coverage report.
- Recorded baseline failures.

Gate:

- A clean environment can install the project without manual dependency repair.
- CI and local commands use the same documented commands.
- No implementation changes begin until the baseline is recorded.

### Phase 1 — Domain models and validation

Deliver:

- Immutable validated domain objects.
- Central validation errors.
- Configuration schema validation.
- CSV and Hugging Face boundary validation.
- Input immutability guarantees.

Gate:

- Invalid shape, type, finiteness, matrix, alpha, price, and configuration cases produce specific errors.
- Caller-owned arrays and dictionaries are not mutated.
- All validation tests pass.

### Phase 2 — Constraints and numerical solver core

Deliver:

- Correct sector and leverage constraints.
- Typed constraint objects.
- Stable linear algebra.
- Solver diagnostics and post-solve feasibility checks.
- Explicit infeasibility and convergence errors.

Gate:

- Every solver result is finite and feasible within tolerance.
- Budget residual is `<= 1e-8`.
- Every configured constraint residual is `>= -1e-8`.
- Singular, indefinite, non-finite, and infeasible inputs fail deterministically.
- Independent reference calculations match within documented tolerances.

### Phase 3 — Backtest engine

Deliver:

- Holdings-based accounting.
- Mark-to-market portfolio values.
- Explicit transaction cost model.
- Rebalance and failure policies.
- Diagnostics for each rebalance.

Gate:

- A positive-return price series increases portfolio value.
- A negative-return series decreases it.
- Transaction costs reduce value by the documented amount.
- Rebalance frequency changes turnover and solver calls as documented.
- Failed rebalances never silently violate constraints.

### Phase 4 — v2 API and CLI

Deliver:

- Polymorphic risk, optimizer, constraint, data-source, and backtest interfaces.
- Clean CLI adapters.
- Structured JSON reports with schema versioning.
- Migration guide from v1.
- Removal of accidental public helpers.

Gate:

- All public exports are documented and tested.
- CLI exit codes are stable and meaningful.
- `--help`, invalid input, infeasible solve, successful solve, plotting, ingestion, and backtest commands are covered.
- Report schema is versioned and validated.

### Phase 5 — Test and CI hardening

Deliver:

- Unit, property, numerical regression, integration, CLI, packaging, and failure-injection tests.
- Coverage enforcement.
- Multi-version CI.
- Wheel installation smoke test.
- Documentation build and link checks.
- Dependency and action review.

Gate:

- Minimum 90% package line coverage.
- Minimum 85% branch coverage for validation, solver, constraint, and backtest modules.
- No untested public class or function.
- Full CI passes on every supported Python version.
- Clean wheel installation and CLI smoke test pass.

### Phase 6 — Documentation rewrite

Deliver:

- Updated architecture documentation.
- API reference generated or verified from code.
- Correct CLI command list.
- Executable examples.
- Numerical guarantees and limitations.
- v1-to-v2 migration guide.
- Updated FAQ, tutorials, fidelity, mismatch, and release docs.

Gate:

- Every canonical documented code example executes in CI; longer tutorials are
  covered by the documentation link/build gate and dedicated integration tests.
- Every documented command exists and returns the documented output shape.
- Every production-readiness claim maps to a test or explicit limitation.

### Phase 7 — Website redesign

Deliver:

- New technical-product visual system.
- Simplified palette and hierarchy.
- Responsive homepage and documentation shell.
- Interactive truthful solver example.
- Accessible navigation, tabs, copy controls, and animation behavior.
- Mobile layouts at 320px, 768px, and 1440px widths.

Gate:

- No horizontal overflow at required viewport sizes.
- All keyboard-accessible controls have visible focus.
- Contrast meets WCAG AA.
- All interactive controls have correct accessible names and states.
- No console errors.
- All internal links return 200.
- Static content remains meaningful with JavaScript disabled.
- Reduced-motion mode disables nonessential animation.
- Lighthouse accessibility score is at least 95.
- Homepage claims and examples match the v2 implementation.
- The header logo and favicon are the same visual system and remain legible at
  32px and 16px-equivalent rendering sizes.
- The architecture “big picture” is an actual responsive graph in the
  rendered page; no ASCII/Markdown flowchart is used for that primary view.
- Production preview has 100/100 Lighthouse accessibility, best practices,
  and SEO scores, with no failed audits and no browser console errors.

### Phase 8 — Release and rollback

Deliver:

- Versioned v2 release.
- Reproducible package artifacts.
- Release checklist.
- GitHub Pages deployment checklist.
- Rollback procedure.
- Changelog and migration notes.

Gate:

- Release candidate passes the complete quality gate.
- Artifacts install and run from a clean environment.
- Site deployment is verified on representative routes.
- Previous stable release remains recoverable.

## 5. Final acceptance criteria

The project is accepted only when all conditions below are true:

- `pytest`, Ruff, Mypy, coverage, package build, wheel install, documentation build, link checks, and site checks pass.
- No known correctness defect from the audit remains open without an explicit documented decision.
- All public APIs have typed contracts and tests.
- All numerical outputs include feasibility and diagnostic information.
- All malformed input and solver-failure paths are deterministic and actionable.
- Backtests correctly account for market movement and costs.
- OOP interfaces and polymorphic implementations are exercised by contract tests.
- Repository guidance, architecture docs, API docs, examples, and website content are consistent.
- Website meets the responsive, accessibility, interaction, and visual criteria above.
- A clean-machine reproduction from documented instructions succeeds.
- The release checklist is completed and rollback is possible.
