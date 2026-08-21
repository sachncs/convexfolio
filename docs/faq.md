# Frequently Asked Questions

Common questions, answered without jargon. If a word confuses you,
look it up in the [Glossary](glossary.md).

---

## General

### What is Convexfolio?

A Python tool that figures out how to split your money across a few
options so your total risk is as small as possible. You give it the
prices, the expected payoffs, and a "how risky is each" matrix; it
gives back the percentages to invest in each.

It's based on the math in a research paper
([arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2)), but you
don't need to read the paper to use the package.

### I'm new to Python / finance / both. Can I still use this?

Yes. Start with the [Getting Started](getting-started.md) guide. It
walks you through everything from "what's a terminal?" to "what do
the numbers mean?". The [Glossary](glossary.md) defines every term
you'll encounter.

### What Python versions work?

Python **3.12 or newer**. Older versions won't install. Newer
versions (3.13+) work.

### Is this package production-ready?

Yes. Convexfolio:

- Is fully type-checked (mypy).
- Is fully lint-checked (ruff).
- Has a deterministic test suite (pytest, 22 tests).
- Has a CI pipeline that runs on every push.
- Uses frozen dataclasses for configuration (can't be silently
  mutated).
- Has reproducible execution (same seed = same output).

That said: **the demo uses synthetic data.** To use Convexfolio with
real options, you'll need to feed in your own market data — see
[Mismatch Report](mismatch_report.md).

---

## Installation

### How do I install it?

```bash
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

That's five commands. The full explanation is in
[Getting Started](getting-started.md#step-3--install-convexfolio).

### What does the package need to run?

Just two things: **NumPy** and **SciPy**. Both come with the install
above. If you write Python that uses matrices, you've probably
already heard of them.

### I'm on Windows. Do the commands change?

Just one: the activation line.

| Step | macOS / Linux | Windows (PowerShell) |
|---|---|---|
| Activate sandbox | `source .venv/bin/activate` | `.venv\Scripts\activate` |

Everything else is the same.

### "ERROR: ... externally-managed-environment"

Your system Python refuses to install packages globally. Fix: use a
virtual environment (which the install steps already create). If you
*really* want to bypass it: `pip install --break-system-packages -e '.[dev]'`,
but only if you understand the risk.

---

## Using it

### How do I solve my first portfolio?

From a Python prompt:

```python
import numpy as np
from convexfolio import Variance, Minimize

precision_matrix = np.array([[2.0, 0.1],
                             [0.1, 1.5]])
cost_vector = np.array([0.60, 0.40])

weights = Minimize(Variance(precision_matrix), cost_vector).value
print(weights)
```

That's it. See [Getting Started](getting-started.md#step-5--run-it-from-python)
for the line-by-line walkthrough.

### What's the difference between Variance and CFVaR?

Both measure risk. **Variance** is the older, simpler one — "how
wildly does the value bounce?" **CFVaR** is a newer, sharper one —
"how bad are the worst outcomes?". CFVaR catches disasters that
variance ignores.

Convexfolio can solve for either:

- `Minimize(Variance(Q), v).value` — minimise variance.
- `CFVaR2Closed(Q, u, v, alpha).value` — minimise CFVaR2.

### What's the budget constraint?

It's a math trick. The rule is: **the weighted sum of prices must
equal exactly 1.** That's `xᵀ v = 1`.

Why? So that every answer is comparable. Without the rule, you could
"minimise risk" by investing $0 — trivially risk-free but useless.
With the rule, all answers spend the same amount, so you can compare
them fairly.

The solvers enforce this automatically. You don't need to do
anything special.

### What does `alpha` mean?

It controls **how cautious the optimiser is**. Smaller alpha = more
cautious (the optimiser is more afraid of bad outcomes). Larger alpha
= more willing to take risks for higher expected reward.

Valid range: between 0 and 0.5. Default: 0.05 (very cautious).

### Can I use a YAML config instead of JSON?

Yes — files ending in `.yaml` or `.yml` work. Install the YAML
support with `pip install '.[yaml]'` (it's already installed if you
ran `pip install -e '.[dev]'`).

### How do I make sure results are reproducible?

Two ways:

1. **Fix the seed** in your config (the default is `7`). Same seed
   + same inputs = same outputs, always.
2. **Run `validate-determinism`** to check:

   ```bash
   convexfolio --command validate-determinism --repetitions 3
   ```

   This runs the pipeline three times and asserts the results are
   byte-identical.

### My numbers are weird. Did something go wrong?

Probably not. The "weights" returned by Convexfolio are **multipliers
on option prices**, not dollar amounts. If you have weights
`[0.65, 0.96]` and prices `[0.60, 0.40]`, that's `$0.39 in A and
$0.39 in B` — close to $1 total, but the raw weights look "bigger
than 1." That's normal.

---

## Troubleshooting

### `command not found: convexfolio`

The sandbox isn't active, or the install didn't complete.

1. `cd convexfolio` (you might be in the wrong folder).
2. `source .venv/bin/activate` (your prompt should show `(.venv)`).
3. `pip install -e '.[dev]'` (re-install if needed).

### `ModuleNotFoundError: No module named 'convexfolio'`

Same as above. The sandbox isn't active.

### The optimisation takes a long time

For small portfolios (5–20 options), it should finish in under a
second. If it's slow:

- Reduce the portfolio size.
- Check that `precision_matrix` is well-conditioned (not too close to
  singular).
- Use `CFVaR2Closed` (closed-form, fast) instead of `CFVaR3Numerical`
  (numerical, slower).

### Results differ between my machine and someone else's

Two possibilities:

1. **Different seed.** Make sure `runtime.seed` is the same in both
   configs.
2. **Floating-point differences.** Different CPUs / NumPy builds can
   give results that agree to 10⁻⁶ but not 10⁻¹⁵. This is normal.

### I get `Optimisation failed`

The solver couldn't find a feasible answer. Common causes:

- `precision_matrix` is singular (rows are linearly dependent).
- `cost_vector` has a zero in it.
- `alpha` is too close to 0 or 0.5.

Try smaller / cleaner inputs first, then re-introduce complexity.

### I get `alpha must satisfy 0 < alpha < 0.5`

Set alpha to a value strictly between 0 and 0.5. The boundary
values are mathematically singular.

---

## Contributing

### How do I run the tests?

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

### How do I check code style?

```bash
ruff check .
```

### How do I check types?

```bash
mypy convexfolio
```

### How do I submit a change?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full workflow.

---

## Support

- **Bug reports / feature requests:** [GitHub Issues](https://github.com/sachncs/convexfolio/issues)
- **Questions / discussion:** [GitHub Discussions](https://github.com/sachncs/convexfolio/discussions)
- **Security issues:** See [SECURITY.md](../SECURITY.md) — please
  don't open a public issue for security problems.
