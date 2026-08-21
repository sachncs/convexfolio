# Glossary

A plain-English dictionary of every term used in this documentation.
If you hit a word you don't recognise, look it up here.

## Money & investing

**Portfolio** — A collection of investments you hold together. For
example, "$1,000 split between two stocks" is a 2-asset portfolio.

**Asset / instrument** — A single investment inside a portfolio. Often
synonyms. In this package, an instrument is one option contract.

**Option** — A contract that gives you the right (not the obligation)
to buy or sell something at a set price by a set date. Options are
what this package prices and combines.

**Weight** — How much of your money goes into each option. If your
portfolio is 60% in option A and 40% in option B, the weights are
`[0.6, 0.4]`.

**Expected payoff** — The average profit you expect from an option
across many possible futures. Sometimes negative — a loss you'd
expect on average.

**Return / payoff vector** — A list of expected payoffs, one per option
in the portfolio. We call it `u`.

**Cost / price vector** — A list of prices, one per option. We call
it `v`. This is what you'd pay to buy one of each option.

## Risk

**Risk** — Chance of losing money. "Lower risk" means a steadier ride,
usually with lower expected reward.

**Variance** — How wildly your portfolio's value bounces around over
time. Low variance = stable. High variance = swings.

**Volatility** — Often used interchangeably with variance. Strictly,
volatility is the standard deviation (square root of variance).

**VaR (Value-at-Risk)** — A traditional risk number: "with 95%
confidence, the worst you could lose in a day is $X."

**CFVaR (Conditional Fractional Value-at-Risk)** — A sharper version
of VaR that catches extreme losses VaR misses. The "fractional" part
weights how bad the loss is, not just whether you crossed a threshold.

**Second-order CFVaR (CFVaR2)** — An approximation of CFVaR that's
fast enough to compute in a single formula. Good enough for most use
cases.

**Third-order CFVaR (CFVaR3)** — A more accurate approximation that
uses numerical optimisation. Slower but more faithful to the paper.

**Tail risk** — The chance of rare-but-disastrous losses. CFVaR is
specifically designed to measure this.

## Math objects

**Matrix** — A rectangular grid of numbers. Think of an Excel sheet.

**Vector** — A list of numbers. Like a single row or column of an
Excel sheet.

**Precision matrix `Q`** — A matrix that captures how risky each
option is (on the diagonal) and how two options move together
(off-diagonal). The math engine of the package works on this.

**Covariance matrix `Σ`** — A closely related cousin of `Q`. Where
`Σ` measures how things wobble together, `Q` measures how certain we
are about the wobble. Bigger `Q` = less wobbly.

**Eigenvalue / eigenvector** — Concepts from linear algebra used
internally by SciPy. You probably don't need to know them to use
Convexfolio.

**Skew-t distribution** — A statistical distribution that captures
"fat tails" — extreme outcomes are more likely than a normal bell
curve predicts.

**Skew-t coefficient `c`** — A scalar that comes out of the skew-t
distribution's formula. Computed by `Compute(degrees_of_freedom)`.

**Linear bias vector `h`** — A vector computed from the covariance
and skewness. Captures the asymmetric part of the distribution.

**Curvature vector `q`** — A vector capturing how the second
derivative of each option contributes to the portfolio.

**Third cumulance `κ₃`** — A scalar measuring the asymmetric "lean"
of the distribution. Zero for symmetric distributions.

**Epsilon-star `ε*`** — The optimal Lagrange multiplier. The magic
number that makes the CFVaR2 closed-form solution work.

## Optimisation

**Optimisation** — Finding the best answer (highest profit, lowest
risk) given constraints. The package's core job.

**Constraint** — A rule the answer must follow. "Total spending must
equal $1" is a constraint.

**Budget constraint** — Specifically, in this package: the weighted
sum of option prices must equal exactly 1 (`xᵀv = 1`). It's a math
trick to make all portfolios comparable.

**Closed-form** — Solved by an exact formula. Run once, get the
answer immediately. No trial-and-error.

**Numerical** — Solved by trial-and-error with a computer. Iterative.
Slower but can handle problems closed-form can't.

**SLSQP** — A specific numerical optimiser provided by SciPy. Stands
for "Sequential Least-SQuares Programming." Used by `CFVaR3Numerical`.

**Objective function** — The thing being minimised (or maximised).
For CFVaR, the objective is the risk number — lower is better.

**Lagrange multiplier** — A mathematical helper that lets you solve
constrained problems by folding the constraint into the objective.

**Composition** — Combining small pieces into a bigger piece. In this
package: `Minimize(Variance(Q), c).value` composes two objects to get
the answer.

## Configuration

**Configuration** — Settings that change how the package runs. Stored
in `config.json` or `config.yaml`.

**Seed** — A starting number for the random number generator. Same
seed = same random sequence = same results. Critical for testing.

**Determinism** — Same inputs always give the same outputs. The
package guarantees this via seeds and frozen dataclasses.

**JSON (`.json`)** — A text format for structured data. Looks like
Python dicts/lists. Used for the default config file.

**YAML (`.yaml` / `.yml`)** — Another text format for structured data.
Less punctuation than JSON. The package also accepts it.

## Python & packaging

**Package** — A reusable bundle of Python code. `convexfolio` is a
package.

**Module** — A single `.py` file inside a package. `convexfolio.math`
is a module.

**Import** — Bringing another module's code into yours.
`from convexfolio import Minimize` imports `Minimize`.

**Dataclass** — A Python type that just holds data, like a struct in
other languages. `Experiment` is a dataclass.

**Frozen** — A dataclass that's read-only after creation. `Experiment`
is frozen — you can't accidentally change it mid-run.

**Class** — A blueprint for creating objects. `Minimize` is a class;
`Minimize(Q, v)` is an instance.

**Instance / object** — A specific concrete thing created from a
class. `m = Minimize(Q, v)` creates an instance.

**Attribute** — A piece of data attached to an instance. `m.value` is
the attribute that holds the answer.

**Method** — A function attached to a class. `Logger().info("hi")`
calls the `info` method.

**Callable** — Anything you can "call" with parentheses. Functions
and class instances with `__call__` are callable.

**Type hint / annotation** — A note saying what type a variable is.
`: float` after a parameter means "this should be a float." Helps
catch bugs before running.

**Mypy** — A tool that checks type hints. Run `mypy convexfolio`.

**Ruff** — A fast linter that catches style issues and bugs. Run
`ruff check .`.

**Pytest** — A tool that runs your tests. Run `pytest -q`.

## Deployment & operations

**CLI (command-line interface)** — Typing commands into a terminal
instead of clicking buttons. The `convexfolio` command is a CLI.

**Terminal / shell / bash** — The text-based window where you type
commands.

**Virtual environment** — An isolated Python sandbox. Keeps this
package's dependencies from breaking other projects.

**venv** — Python's built-in tool for creating virtual environments.

**pip** — Python's package installer. `pip install` puts packages
into your active environment.

**PyPI** — The public registry where Python packages live. (Not used
by this package — install from source.)

**Source distribution / sdist** — A `.tar.gz` archive containing the
package's source code.

**Wheel** — A `.whl` file. A pre-built version of a package, faster
to install than a source distribution.

**systemd** — Linux's built-in service manager. Runs programs
automatically at boot or on a schedule.

**cron** — Linux's scheduler for repeating tasks ("every day at 2 AM").

**Docker** — A way to package software so it runs the same on every
machine.

**Dockerfile** — A recipe file telling Docker how to build your
software's container.

**Container / image** — A standalone, ready-to-run bundle built from
a Dockerfile.

## Project

**Repository (repo)** — The folder containing your code, plus its
full history of changes.

**Commit** — A snapshot of the code at one point in time, with a
message describing what changed.

**Branch** — A parallel line of development. `master` is the main one.

**Tag** — A named pointer to a specific commit, usually a release.
`v1.2.3` is a typical tag.

**SemVer (Semantic Versioning)** — A version-number convention:
`MAJOR.MINOR.PATCH`. Bump MAJOR for breaking changes, MINOR for new
features, PATCH for bug fixes.

**Changelog** — A file (`CHANGELOG.md`) listing every notable change
in each release.

**Issue** — A bug report or feature request on GitHub.

**Pull request (PR)** — A proposed change submitted to the project
for review.
