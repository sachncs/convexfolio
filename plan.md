# Production-Readiness Plan — `optimal-option-portfolios`

**Repository:** `/Users/sachin/repo/optimal-option-portfolios`
**Target version:** `0.3.0` (classifier `5 - Production/Stable`)
**Mode:** atomic commits, one identifier (or one logical unit) per commit
**Status:** locked; 53 commits across 6 phases

---

## Goal

Make the repository **readable** and **reliable** for production use.

### Non-negotiable rules (binding throughout)

1. **No semi-private naming.** No leading-underscore on top-level names (`_helper`, `_validate_internal`, etc.). No `__dunder__` other than Python-mandated. Public surface declared explicitly via `__all__` in `options/__init__.py`.
2. **No `try/except` without a typed reason.** Catch only specific named exceptions (`ValueError`, `FileNotFoundError`, `json.JSONDecodeError`, etc.). Never `except Exception:` or bare `except:`. If something must be caught, it must be rethrown as a typed error.
3. **Elaborative locals.** Math shorthand is banned. `g1`/`g2`/`q`/`eps_star`/`nu`/`sigma`/`omega`/`theta`/`m`/`x`/`z`/`psi`/`tau`/`kappa3` are forbidden as identifier names. Replacement names use full words (`loss_gradient`, `precision_matrix`, `optimal_epsilon`, `degrees_of_freedom`, `covariance`, `skewness`, `price_drift`, `instrument_count`, `weights`, `z_score`, `dual_variable`, `tau`, `third_order_cumulant`).
4. **No new abstraction.** No `Builder`/`Manager`/`Factory`/`Strategy`/`Handler`/`Service`/`Helper`/`Util` suffixes. No ABC, no `Protocol`, no `isinstance` dispatch, no closure factories. Inline closures where they fit; hoist the rest as module-level functions.
5. **Pinned dependencies stay loose.** Loose floors only; no lockfile.
6. **One commit per identifier rename.** Larger logical changes (rename dataclass, hoist closure, add module) get their own commit. Each commit must leave the tree green.

---

## Decisions baked in

| Topic | Decision |
|---|---|
| `options/pricing.py` | **Delete outright.** No test, no export. Drops 4 functions from any future API surface. |
| `compare_cfvar2_solution_quality` | **Rename to `quality_score`.** Two-word but elaborative. Elaboration wins. |
| `ExperimentConfig` / `RuntimeConfig` / `OptimizationConfig` | **Flatten to one `Experiment` dataclass:** `seed`, `alpha`, `repetitions`, `output_directory`, `log_level`. |
| Old config JSON shape | **Hard break at 0.3.0.** `load(path)` reads flat keys only; old keys raise `ValueError` with a clear message. |
| `OOP_*` env vars | **Drop from README and `.env.example`.** Never wired; deleting the lie. |
| `.env.example` content | **Delete the env-var rows**; the file remains as a stub or is deleted. |
| Moments module split | **Cancel.** Keep one `moments.py`. Rename functions inside to descriptive single names (`c`, `h`, `q`, `hg`, `eg`). |
| Closures | **Hoist as module-level functions** with Google-style docstrings (7 instances). |
| `mycoverage.pyc`-type issues | **Untrack all `__pycache__/`** and add `.gitignore` enforcement. |
| Sphinx extra | **Wire up `conf.py` + `index.rst`** in `docs/`, otherwise drop the `docs` extra from `pyproject.toml`. |
| CI Python matrix | **3.10 / 3.11 / 3.12.** |
| Tooling strictness | **`mypy --strict`, `ruff check`, `ruff format --check`.** Loose floors only. |
| Lockfile | **None.** Dependabot weekly bumps only. |
| README CI badge | **`?branch=main`** (was `master`). |
| `experiments` package surface | **Bump to 0.3.0; classifier to `5 - Production/Stable` after Phase D passes.** |

---

## Phase summary

| Phase | Purpose | Commits |
|---|---|---|
| R | Reliability foundation: stop the lies, version bump, conventions | 9 |
| V | Variable elaboration across `options/` | 10 |
| H | Closure hoisting | 7 |
| F | Google-style docstrings (one per module) | 11 |
| C | Hardening: mypy, ruff, CI, error wrapping | 12 |
| D | Verify, build, smoke-test, classifier bump | 3 |
| **Total** | | **52** |

Plus 1 dedicated doc-fix commit listed in Phase F for index/api-reference sync = **52 atomic commits**.

---

## Phase R — Reliability foundation

**Outcome:** tree is honest. Tracked bytecode gone. API table matches code. Version and CI correct. Contracts documented.

### Acceptance criteria

- [ ] `git ls-files | grep __pycache__` returns zero results.
- [ ] `find . -name __pycache__ -type d` returns empty for `src/` and `tests/`.
- [ ] `options/py.typed` exists; `pip install dist/oop-0.3.0.whl && python -c "import options; reveal_type(oop.solve_variance_minimization)"` returns a non-`Any` type.
- [ ] `pyproject.toml` `version = "0.3.0"`.
- [ ] README CI badge uses `?branch=main`.
- [ ] `options/pricing.py` does not exist; `git log --follow -- options/pricing.py` shows the deletion.
- [ ] `grep -r 'OOP_' .` returns zero matches in `src/` (env-var docs and `.env.example` removed).
- [ ] `rg -n '_[a-z]' options/` returns only Python-mandated dunders (`__init__`, `__all__`, `__post_init__`, `__pycache__`).
- [ ] `CONTRIBUTING.md` lists the no-`_`-prefix, no-bare-`except`, elaborative-locals contract.
- [ ] `.github/workflows/ci.yml` has `python-version: ["3.10", "3.11", "3.12"]` strategy.
- [ ] `artifacts/reproduction_report.json` is untracked; `artifacts/.gitkeep` exists.

---

## Phase V — Variable elaboration

**Outcome:** every identifier in `options/` and `tests/` is descriptive. No math shorthand survives.

### Per-file rename manifest

| File | Renames |
|---|---|
| `options/optimization.py` | `g1`→`loss_gradient`; `g2`→`constraint_gradient`; `eps_star`→`optimal_epsilon`; `eps_plus`/`eps_minus`→`epsilon_plus`/`epsilon_minus`; `acal`/`bcal`/`ccal`→`coeff_a`/`coeff_b`/`coeff_c`; `ascr`/`bscr`/`cscr`→`score_a`/`score_b`/`score_c`; `disc`→`discriminant`; `denom`→`denominator`; `psi_star`→`optimal_dual`. |
| `options/risk.py` | `sigma`→`covariance`; `omega`→`skewness` (where it's a vector); `tau`→`tau`; `core`→`linear_core_term`; `qmatrix` argument→`precision_matrix`. |
| `options/reproduction.py` | `theta_vector`→`price_drift`; `d`→`delta_matrix`; `gamma_tensor`→`third_derivative`; `nu`→`degrees_of_freedom`; `c_scalar`→`c_coefficient`; `p_vector`→`pricing_vector`; `b`→`budget_matrix`; `xi_vector`→`xi_intercept`; `zeta`→`zeta_intercept`; `u`→`dual_residual`; `r`→`residual_matrix`; `umatrix`→`uncertainty_matrix`; `q_tilde`→`q_symmetric_part`; `eps_star`→`optimal_epsilon`; `variance_at`→`direct_variance` (in hoist commit). |
| `options/moments.py` | `m`→`instrument_count`; `gamma`→`third_derivative` where it's a tensor input. |
| `options/pipeline.py` | `random_matrix`→`sample_matrix`; `kappa3_callback`→`kappa3_callback`; `initial_x`→`initial_weights`; `instrument_count`→`n_instruments`; `mock_kappa3` function ref replaced by `lambda x: 0.0`. |
| `options/cli.py` | `cfg`→`experiment`; `summary`→`determinism_summary`; `path`→`output_path`; `args`→`parsed_args`. |
| `options/determinism.py` | `is_equal`→`all_match`; `serialized`→`serialized_reports`. |
| `options/config.py` | `payload`→`raw_config`; `runtime`/`optimization` (locals)→`runtime_config`/`optimization_config` to mirror types during deprecation window. |
| `tests/test_*.py` | Elaboration of every local that survives from source. ~5 atomic commits. |

### Acceptance criteria

- [ ] `rg -nw 'g1|g2|q|eps_star|nu|sigma|omega|theta|psi|tau|m|x|z' options/` returns only false positives (`nu` inside a docstring, `m` inside a regex, etc.) — no identifier hits.
- [ ] `python -c "from options.optimization import loss_gradient, optimal_epsilon"` works (renames don't shadow module globals).
- [ ] All tests still pass.

---

## Phase H — Closure hoist

**Outcome:** no closures in `options/`. All factory wrappers gone. Each hoisted function carries a Google-style docstring.

### Hoist manifest

| Hoisted function | Source closure | Args |
|---|---|---|
| `loss_term(eps, loss_grad, constraint_grad, precision, optimal_eps)` | `optimization.py` `variance_term` (line ~42) | scalars + 1-D |
| `score(eps, loss_grad, constraint_grad, precision, optimal_eps)` | `optimization.py` `objective` (line ~45) | scalars + 1-D |
| `objective(x, alpha, u, precision, kappa3_callback)` | `optimization.py` `objective` (line ~108) | 1-D + scalars |
| `direct_variance(xvec, theta, delta, third_deriv, mu, cov, dof, c_coef, h_vec)` | `reproduction.py` `variance_at` (line ~115) | 1-D + many 1-D/2-D |
| `normalizer_integrand(z, sigmat, density, xp, xc, pp, pc)` | `pricing.py` `integrand` (line ~31) | scalar + scalars |
| `call_integrand(val, spot_price, strike, risk_free_rate, maturity, sigmat, density)` | `pricing.py` `integrand` (line ~55) | scalar + scalars |
| `put_integrand(val, spot_price, strike, risk_free_rate, maturity, sigmat, density)` | `pricing.py` `integrand` (line ~79) | scalar + scalars |
| `mock_kappa3` deleted | `pipeline.py` (line ~38) | inline `lambda x: 0.0` at call site |

### Acceptance criteria

- [ ] `rg -nP '^\s+def ' options/` returns zero results — no nested function defs remain.
- [ ] Each hoisted module-level function has a Google-style docstring (one-line summary, `Args:`, `Returns:`, `Raises:` as applicable).
- [ ] `solve_cfvar3_numerical` body in `options/optimization.py` references `objective` as a top-level import; no closure creation.
- [ ] `compare_cfvar2_solution_quality` → `quality_score(alpha, u, v, precision)` rename done in Phase V commit 30; body copied across.
- [ ] All tests pass.

---

## Phase F — Google-style docstrings

**Outcome:** every module, every public class, every public function has a Google-style docstring. Format:

```
"""One-line imperative summary.

Optional longer description.

Args:
    param1: Meaning, units, constraints.
    param2: Meaning, units, constraints.

Returns:
    Meaning, dtype, shape.

Raises:
    ValueError: When ``alpha`` is outside (0, 1).
"""
```

### Modules covered (one commit per module)

| # | Module | Symbols |
|---|---|---|
| 27 | `options/config.py` | `Experiment`, `load`, `validate` |
| 28 | `options/moments.py` | `c`, `h`, `q`, `hg`, `eg` |
| 29 | `options/risk.py` | `validate_shapes`, `expectation_linear`, `variance_quadratic`, `cfvar2`, `cfvar3`, `kappa3` |
| 30 | `options/optimization.py` | `solve_variance_minimization`, `compute_epsilon_star`, `solve_cfvar2_closed_form`, `solve_cfvar3_numerical`, `build_cfvar3_objective`, `quality_score`, `loss_term`, `score`, `objective` |
| 31 | `options/reproduction.py` | `greeks`, `variance_direct_formula`, `linearize`, `reconstruct`, `direct_variance` |
| 32 | `options/pipeline.py` | `run_reproduction`, `save_report` |
| 33 | `options/determinism.py` | `deterministic_report` |
| 34 | `options/logging.py` | `configure_logging` |
| 35 | `options/cli.py` | `parser`, `main` |
| 36 | `options/types.py` | `FloatArray` alias |
| 37 | `docs/`: api-reference + index sync | — |

### Acceptance criteria

- [ ] Every public function in `options/` has a `"""..."""` docstring.
- [ ] Every public function with parameters has an `Args:` block.
- [ ] Every public function with a non-`None` return has a `Returns:` block.
- [ ] Every public function that raises a named exception has a `Raises:` block.
- [ ] `python -c "from options import solve_variance_minimization; help(solve_variance_minimization)"` renders the docstring cleanly.
- [ ] `interrogate options/` (interrogate-style count) reports coverage ≥ 100% of public symbols.

---

## Phase C — Hardening

**Outcome:** static analysis is enforced; CLI behaves predictably on bad input.

### Acceptance criteria

- [ ] `pyproject.toml` `[tool.mypy]` has `strict = true`.
- [ ] `pyproject.toml` `[tool.ruff.lint]` has `select = ["E","F","W","I","B","UP","C4","SIM"]`.
- [ ] `ruff check src tests scripts` exits 0.
- [ ] `ruff format --check src tests scripts` exits 0.
- [ ] `mypy options` exits 0.
- [ ] `.github/workflows/ci.yml` runs `ruff format --check` step.
- [ ] `.github/workflows/ci.yml` `on.push.branches: ["main"]` only.
- [ ] `.github/workflows/ci.yml` uses `actions/setup-python` with `cache: "pip"`.
- [ ] `options --version` prints the package version.
- [ ] `options --command reproduce-report` with a missing config exits non-zero with a typed error message.
- [ ] `options --command reproduce-report` with invalid JSON exits non-zero with `json.JSONDecodeError` message.
- [ ] `options --command reproduce-report` with `alpha: 1.5` exits non-zero with `ValueError` message.
- [ ] No `except` clause without a specific named exception (audit before commit).
- [ ] `.github/CODEOWNERS` exists with `@sachncs` mapped.
- [ ] `.github/ISSUE_TEMPLATE/config.yml` exists and wires the chooser.
- [ ] `pyproject.toml` uses `license = "MIT"` + `license-files = ["LICENSE"]` (SPDX form).

---

## Phase D — Verify + release

**Outcome:** package builds, wheel installs, CLI works end-to-end across supported Python versions. Classifier bumped.

### Acceptance criteria

- [ ] `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q` exits 0 on Python 3.10, 3.11, 3.12.
- [ ] `ruff check`, `ruff format --check`, `mypy options --strict` all exit 0 on Python 3.12.
- [ ] `python -m build` produces `dist/oop-0.3.0-py3-none-any.whl` and `dist/oop-0.3.0.tar.gz`.
- [ ] `pip install dist/oop-0.3.0-py3-none-any.whl` succeeds into a fresh venv.
- [ ] `options --help` exits 0.
- [ ] `options --command reproduce-report` produces `artifacts/reproduction_report.json` matching the prior baseline structure.
- [ ] `options --command validate-determinism` exits 0 with `deterministic: true`.
- [ ] `pyproject.toml` `version = "0.3.0"`.
- [ ] `pyproject.toml` classifier `Development Status :: 5 - Production/Stable`.
- [ ] `CHANGELOG.md` has a `[0.3.0]` section with explicit `BREAKING` subsection listing:
  - removed: `truncated_density`, `compute_z_normalizer`, `skew_gosset_call_price`, `skew_gosset_put_price`, all `pricing.py` symbols;
  - renamed: `compare_cfvar2_solution_quality` → `quality_score`;
  - class shape: `ExperimentConfig`/`RuntimeConfig`/`OptimizationConfig` collapsed into `Experiment` (fields: `seed`, `alpha`, `repetitions`, `output_directory`, `log_level`);
  - config JSON: flat keys required; old keys raise `ValueError`.
- [ ] No `git tag` created until user explicitly approves.

---

## Commit ledger (52 atomic commits)

### R (9)

1. `chore: untrack options/__pycache__ and tests/__pycache__`
2. `docs(readme): fix API table to match actual exports`
3. `feat(types): add py.typed marker`
4. `chore: bump version 0.2.0 → 0.2.1`
5. `fix(ci): badge branch master → main`
6. `chore: untrack artifacts/reproduction_report.json, add artifacts/.gitkeep`
7. `chore(refactor): delete options/pricing.py`
8. `ci: Python matrix 3.10 / 3.11 / 3.12`
9. `chore: add CONTRIBUTING.md naming and error-handling contract`

### V (10)

10. `refactor(optimization): elaborative locals`
11. `refactor(risk): elaborative locals`
12. `refactor(reproduction): elaborative locals`
13. `refactor(moments): elaborative locals`
14. `refactor(pipeline): elaborative locals`
15. `refactor(cli): elaborative locals`
16. `refactor(determinism): elaborative locals`
17. `refactor(config): elaborative locals`
18. `refactor(tests): elaborative locals (test_optimization)`
19. `refactor(tests): elaborative locals (test_risk, test_config, test_determinism, test_determined_quantities)`

### H (7)

20. `refactor(optimization): hoist loss_term to module level`
21. `refactor(optimization): hoist score to module level`
22. `refactor(optimization): hoist objective for cfvar3 to module level; rename compare → quality_score`
23. `refactor(reproduction): hoist direct_variance to module level`
24. `refactor(pipeline): inline mock_kappa3 as lambda`
25. `refactor: confirm no nested function defs remain (audit commit)`
26. `docs: cross-check __all__ matches test imports`

### F (11)

27. `docs(config): Google-style docstrings`
28. `docs(moments): Google-style docstrings`
29. `docs(risk): Google-style docstrings`
30. `docs(optimization): Google-style docstrings`
31. `docs(reproduction): Google-style docstrings`
32. `docs(pipeline): Google-style docstrings`
33. `docs(determinism): Google-style docstrings`
34. `docs(logging): Google-style docstrings`
35. `docs(cli): Google-style docstrings`
36. `docs(types): Google-style docstring`
37. `docs: api-reference and index sync with re-exports`

### C (12)

38. `chore(mypy): strict = true`
39. `chore(ruff): select = E,F,W,I,B,UP,C4,SIM`
40. `chore: ruff autofixes across src and tests`
41. `ci: ruff format --check`
42. `ci: narrow push trigger to main`
43. `ci: setup-python pip cache`
44. `feat(cli): --version and typed error wrapping`
45. `test(cli): subprocess tests for happy and error paths`
46. `chore: license = "MIT" + license-files`
47. `chore: add .github/CODEOWNERS`
48. `chore: add .github/ISSUE_TEMPLATE/config.yml`
49. `chore: bump version 0.2.1 → 0.3.0`
50. `docs(CHANGELOG): [0.3.0] BREAKING section`

### D (3, manual gate)

51. `chore: fix any lint/format/mypy/pytest gaps surfaced during Phase D check`
52. `chore: build wheel and verify install + smoke-test`
53. `chore: classifier 4 - Beta → 5 - Production/Stable`

---

## Risks / halt conditions

- **`mypy --strict` annotation gaps.** `numpy` call results will surface ~10–30 missing annotations across `optimization.py`, `risk.py`, `reproduction.py`, `moments.py`. Each fix is 1–3 lines; absorb into the commit that surfaced it.
- **Closure hoist correctness.** `solve_cfvar3_numerical` calls its objective in an inner loop. The hoisted `objective(x, alpha, u, precision, kappa3_callback)` is passed scalars on each iteration — verify solver performance doesn't regress (it shouldn't; the closure captured the same scalars).
- **`Experiment` field name collisions.** `output_dir` previously a local in `pipeline.py` and `save_report(report, output_dir)` is a parameter — once we flatten to `experiment.output_directory`, every `config.output_dir` becomes `experiment.output_directory`. Phase V catches this.
- **Tolerant JSON or hard break.** The user picked hard break at 0.3.0. `load(path)` raises `ValueError` with a one-line message. Users upgrading from 0.2.x will see the error and re-write their config.
- **Pricing deletion.** No callers in src/ or tests/. Safe deletion. Verify with `rg "from options.pricing|import pricing|truncated_density|compute_z_normalizer|skew_gosset_call_price|skew_gosset_put_price" .` returns zero before commit 7.

---

## Stop conditions (binding)

- **Pause for review** at the end of phases R, V, H, F, C before starting the next phase.
- **Stop immediately** if any commit leaves `ruff check`, `ruff format --check`, `mypy options --strict`, or `pytest -q` failing. Do not stack commits on a red tree.
- **No `git tag`** without explicit go-ahead.
- **No `git push`** without explicit go-ahead.
- **No commit message past tense** ("renamed"), no co-author stamps added by tooling, no emoji, no AI-generated trailers.

---

## Acceptance summary (top-level, single block)

The plan is complete when:

1. Tree is green on Python 3.10, 3.11, 3.12 across `ruff check`, `ruff format --check`, `mypy options --strict`, `pytest -q`.
2. `python -m build && pip install dist/oop-0.3.0-py3-none-any.whl` succeeds; `options --help`, `options --command reproduce-report`, `options --command validate-determinism` all exit 0.
3. `options/` contains no `_`-prefix names, no closure factories, no math shorthand identifiers, no bare/over-broad `except`.
4. `options/__init__.py` declares `__all__` matching actual public symbols; `__init__.py` exports are written identically in `docs/api-reference.md`.
5. Public API (post-`pricing.py` deletion) is 17 symbols, every one elaborative: `solve_variance_minimization`, `compute_epsilon_star`, `solve_cfvar2_closed_form`, `solve_cfvar3_numerical`, `build_cfvar3_objective`, `quality_score`, `validate_shapes`, `expectation_linear`, `variance_quadratic`, `cfvar2`, `cfvar3`, `kappa3`, `c`, `h`, `q`, `hg`, `eg`. Plus `Experiment`, `load`, `validate`, `reproduce`/`run_reproduction`, `save_report`, `deterministic_report`, `configure_logging` as supporting public surface.
6. `CHANGELOG.md` `[0.3.0]` section documents every breaking change with old→new mappings.
7. `pyproject.toml` declares version `0.3.0` and classifier `5 - Production/Stable`.

When the above are true, the repository is production-ready.
