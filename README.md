<p align="center">
  <h1 align="center">Convexfolio</h1>
  <p align="center">A Python package that figures out how to spread your money across options to minimise risk.</p>
  <p align="center">
    <a href="#installation"><img src="https://img.shields.io/badge/python-3.12%20%7C%203.13-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
    <a href="https://github.com/sachncs/convexfolio/releases/latest"><img src="https://img.shields.io/github/v/release/sachncs/convexfolio" alt="Latest release"></a>
    <a href="https://github.com/sachncs/convexfolio/actions"><img src="https://img.shields.io/github/actions/workflow/status/sachncs/convexfolio/ci.yml?branch=main" alt="CI"></a>
    <a href="https://github.com/sachncs/convexfolio/pkgs/container/convexfolio"><img src="https://img.shields.io/badge/ghcr.io-convexfolio-blue" alt="Docker image"></a>
    <a href="https://github.com/sachncs/convexfolio/stargazers"><img src="https://img.shields.io/github/stars/sachncs/convexfolio" alt="Stars"></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Ruff"></a>
    <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type%20checked-mypy-blue.svg" alt="mypy"></a>
  </p>
</p>

---

## What is this?

Convexfolio is a small Python tool that answers one question:

> *"Given a handful of options to choose from, how should I split my
> money between them so my risk is as small as possible?"*

You feed it the prices, the expected payoffs, and a "how risky is each
option" matrix. It hands you back the **weights** — the percentage of
your money that should go into each option.

It implements the math from a research paper
([arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2)). You don't
need to read the paper to use the package.

---

## Who is this for?

You, even if:

- You've never written Python before.
- You don't know what an "option" is in finance.
- You've never heard the word "portfolio".

If you can install Python and type commands into a terminal, you can
use Convexfolio. When the docs use a word you don't know, look it up
in the [Glossary](docs/glossary.md).

If you've used Python before, you'll be productive in five minutes.

---

## What can it do?

- **Variance minimisation** — Finds weights that minimise how wildly
  your portfolio value bounces around. ([Glossary: variance](docs/glossary.md))
- **CFVaR2 (closed-form)** — A faster, smarter risk measure with an
  exact formula. ([Glossary: CFVaR](docs/glossary.md))
- **CFVaR3 (numerical)** — A more accurate risk measure, solved
  numerically. ([Glossary: SLSQP](docs/glossary.md))
- **Deterministic execution** — Same inputs always give same
  outputs. ([Glossary: determinism](docs/glossary.md))
- **Command-line tool** — Run reports from the terminal without
  writing Python. ([Glossary: CLI](docs/glossary.md))
- **JSON / YAML configuration** — Tweak settings in a plain text
  file. ([Glossary: JSON](docs/glossary.md))

---

## Before you start

You'll need Python **3.12 or newer** installed on your computer.

If you don't know what Python is or whether you have it:

1. Open a terminal (on macOS: `Cmd + Space`, type "Terminal"; on
   Windows: open "PowerShell"; on Linux: open your usual terminal).
2. Type `python3 --version` and press Enter.
3. If you see a version number starting with `3.12` or `3.13`, you're
   set.
4. If you see "command not found" or an older version, follow the
   [official Python installer guide](https://realpython.com/installing-python/).

You'll also need **git** (a tool for downloading code). Same drill:
type `git --version` in your terminal.

---

## Installation

Pick whichever option fits your setup:

### Option 1 — Pre-built wheel from GitHub Releases (fastest)

```bash
pip install https://github.com/sachncs/convexfolio/releases/download/v0.3.0/convexfolio-0.3.0-py3-none-any.whl
```

No `git clone`, no build step. Works as soon as a GitHub Release
exists.

### Option 2 — Docker (no Python install needed)

```bash
docker run --rm ghcr.io/sachncs/convexfolio --command print-report
```

The image bundles Python + Convexfolio + its dependencies. Useful on
servers or when you can't (or don't want to) install Python locally.

### Option 3 — From source (recommended for development)

A "virtual environment" is an isolated Python sandbox that keeps this
package's stuff from interfering with your other Python projects.
([Glossary: virtual environment](docs/glossary.md))

```bash
# 1. Download the code
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio

# 2. Make a sandbox for it
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows (PowerShell)

# 3. Install Convexfolio and its dev tools
pip install -e '.[dev]'
```

> 💡 **The dot in `.[dev]` is intentional.** It means "install this
> package and also the dev extras." The square brackets are part of
> the command, not punctuation.

After this, your terminal prompt will probably have `(.venv)` at the
front. That tells you the sandbox is active. To leave the sandbox
later, type `deactivate`.

---

## Your first run — the command line

The fastest way to see Convexfolio work. No Python required:

```bash
convexfolio --command print-report
```

You'll see a long JSON blob print to your terminal. That JSON is a
**report** describing a sample portfolio that Convexfolio analysed.
Don't worry about understanding it yet — we'll walk through it in the
[Getting Started guide](docs/getting-started.md).

You can also generate a JSON file instead of printing to the screen:

```bash
convexfolio --command reproduce-report
ls artifacts/
cat artifacts/report.json
```

---

## Your first run — Python

Open a Python interpreter (`python3` in your terminal) and try this:

```python
import numpy as np                              # numpy is a math library
from convexfolio import Variance, Minimize      # import the solver

# Imagine you have $1 to split between two options.
# Option A costs $0.60, Option B costs $0.40.
# The "precision matrix" below captures how risky each option is
# (2.0 = riskier for A, 1.5 = less risky for B) and how they
# wobble together (0.1 = barely related).
precision_matrix = np.array([[2.0, 0.1],
                             [0.1, 1.5]])
cost_vector = np.array([0.60, 0.40])

# Ask Convexfolio: how do I split to minimise risk?
answer = Minimize(Variance(precision_matrix), cost_vector).value
print(answer)
```

You'll see something like `[0.65, 0.95]`. That means:

- ~65% of your money in option A
- ~95% of option B (relative to its $0.40 price)

Translated into actual dollars out of $1: roughly **$0.52 in A and
$0.48 in B** (because option B is cheaper, you buy more of it). The
exact dollar split doesn't matter — what matters is that Convexfolio
found the lowest-risk combination.

The full walk-through with explanations of every line lives in
[Getting Started](docs/getting-started.md).

---

## Configuration

Want to change something? Create a file called `config.json` in your
project folder:

```json
{
  "runtime": {
    "seed": 7,
    "log_level": "INFO",
    "output_directory": "artifacts"
  },
  "optimization": {
    "alpha": 0.05,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
```

Then pass it to Convexfolio:

```bash
convexfolio --config config.json --command reproduce-report
```

What each field means:

| Field | Plain English |
|---|---|
| `runtime.seed` | A starting number for the random generator. Change it to get different sample data; keep it the same to get reproducible results. |
| `runtime.log_level` | How chatty the package should be: `DEBUG` (very chatty), `INFO` (normal), `WARNING` (only problems), `ERROR` (only failures). |
| `runtime.output_directory` | Where to save the report file. |
| `optimization.alpha` | "How cautious do you want the optimiser to be?" Smaller = more cautious. Must be between 0 and 0.5. |
| `optimization.method` | Which solver to run: `variance`, `cfvar2`, `cfvar3`, or `all` (run everything). |
| `optimization.enforce_nu_greater_than_six` | If `true`, refuse to run unless the math parameters are well-behaved. |

---

## Where to go next

- **[Getting Started](docs/getting-started.md)** — A complete
  beginner's walk-through, building your first portfolio step by step.
- **[FAQ](docs/faq.md)** — Common questions answered in plain
  English.
- **[Glossary](docs/glossary.md)** — Every technical term, defined.
- **[API Reference](docs/api-reference.md)** — The full list of
  classes and functions, with examples. Bookmark this once you start
  writing real code.
- **[Architecture](docs/architecture.md)** — How the package is put
  together, for the curious.

For operators / maintainers:

- **[Deployment](docs/deployment.md)** — Run Convexfolio on a server.
- **[Release process](docs/release.md)** — How new versions get
  published.
- **[Fidelity report](docs/fidelity_report.md)** — Does the code
  match the paper?
- **[Research determination](docs/research_determination.md)** —
  Which math quantities are well-defined vs assumed.
- **[Mismatch report](docs/mismatch_report.md)** — Known
  differences between the package and the paper.

---

## Contributing

Want to improve Convexfolio? See [CONTRIBUTING.md](CONTRIBUTING.md) for
how to set up a development environment and submit changes.

## Code of Conduct

We expect everyone to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Found a security issue? See [SECURITY.md](SECURITY.md) — please don't
open a public GitHub issue for security problems.

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, ship it.
