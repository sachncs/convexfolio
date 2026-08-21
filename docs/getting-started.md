# Getting Started

By the end of this guide you'll have:

1. Installed Convexfolio.
2. Run it once from the terminal.
3. Run it once from Python.
4. Changed one setting and seen what happened.

No prior knowledge required. Every command is explained.

> 📖 **Stuck on a word?** Look it up in the
> [Glossary](glossary.md). It defines every term used here.

---

## What you'll need

Before you start, make sure you have:

- **A computer** running macOS, Linux, or Windows.
- **Python 3.12 or newer.** Type `python3 --version` in your
  terminal. If you see an older number or "command not found", follow
  [this guide](https://realpython.com/installing-python/).
- **git** for downloading code. Type `git --version`. Same drill if
  it's missing — install from [git-scm.com](https://git-scm.com/).
- **A terminal.** macOS: Terminal.app. Windows: PowerShell. Linux:
  whatever you usually use.

That's it.

---

## Step 1 — Get the code

Open your terminal and run:

```bash
git clone https://github.com/sachncs/convexfolio.git
cd convexfolio
```

What just happened:

- `git clone` **downloads** a copy of the Convexfolio source code
  into a new folder called `convexfolio`.
- `cd convexfolio` **moves you into** that folder. From now on, every
  command assumes you're inside it.

> 💡 **Tip:** Type `ls` (macOS/Linux) or `dir` (Windows) to see
> what's inside the folder. You should see files like `README.md`,
> `pyproject.toml`, and a folder called `convexfolio/`.

---

## Step 2 — Make a sandbox

A "virtual environment" is an isolated Python sandbox so this
project's packages don't interfere with your other Python projects.

```bash
# Create the sandbox
python3 -m venv .venv

# Activate it
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell
```

You'll know it worked when your terminal prompt shows `(.venv)` at
the front. From now on, every `pip install` puts packages into this
sandbox, not your system Python.

> 📝 **Heads-up:** If you close your terminal and come back later,
> you'll need to `cd convexfolio` and re-run the `source` line to get
> back into the sandbox.

---

## Step 3 — Install Convexfolio

```bash
pip install -e '.[dev]'
```

What this does:

- `pip install` — Python's package installer. Think of it as an app
  store for Python.
- `-e` — "editable" mode. Edits to the source code take effect
  immediately without re-installing.
- `'.[dev]'` — Install this package (`.[dev]`) plus the dev extras
  (testing tools, linters). The `.` means "the current folder."

If you see a wall of text scroll past, that's normal. If it ends with
"Successfully installed ...", you're good.

> ⚠️ **If you see "ERROR: ..." at the end**, something went wrong.
> Common causes:
> - Forgot to activate the sandbox (no `(.venv)` in your prompt)?
> - Python too old? Re-run `python3 --version`.
> - On macOS and pip complains about "externally-managed-environment"?
>   Re-run with `pip install --break-system-packages -e '.[dev]'` —
>   but only if you understand what that does.

---

## Step 4 — Run it from the terminal

Try the simplest command:

```bash
convexfolio --command print-report
```

You should see a JSON blob printed to your terminal. Don't worry
about reading it yet — just confirm Convexfolio runs.

That JSON describes a sample portfolio that Convexfolio just solved.
The structure:

```json
{
  "config":  { ... },          // The settings you used
  "inputs":  { "u": [...],     // Expected payoffs (one per option)
               "v": [...],     // Prices (one per option)
               "qmatrix": [...] },  // The "how risky is each" matrix
  "outputs": { "variance_weights": [...],   // The recommended split
               "cfvar2_weights": [...],     // A risk-aware split
               "cfvar3_weights": [...],     // Another risk-aware split
               "cfvar2_at_variance_weights": 0.97 },  // The risk score
  "uncertainty": { "status": "ASSUMPTION", ... }
}
```

Now save it to a file instead:

```bash
convexfolio --command reproduce-report
ls artifacts/
cat artifacts/report.json
```

A new folder called `artifacts/` appeared. Inside is `report.json` —
the same report, saved to disk.

> 🎉 **You just ran your first portfolio optimisation.**

---

## Step 5 — Run it from Python

Open a Python prompt:

```bash
python3
```

You'll see something like `>>>`. That's the Python prompt waiting for
you.

### The story

> You have **$1** to split between **two options**.
>
> Option A costs **$0.60**. It's a bit risky.
> Option B costs **$0.40**. It's a bit less risky.
>
> They're slightly correlated — when A goes up, B tends to go up
> too (just less).
>
> **Question:** How much should you put in each option to keep your
> risk as low as possible?

### The code

Type this line by line (don't copy-paste, so you feel what each line
does):

```python
import numpy as np
```

`numpy` is Python's standard math library. We need it for matrices.

```python
from convexfolio import Variance, Minimize
```

Pull in the two pieces we'll use: `Variance` (the "how risky" idea)
and `Minimize` (the solver).

```python
# Set up the problem.
# The 2x2 matrix says:
#   - A is somewhat risky (2.0 on the diagonal)
#   - B is less risky    (1.5 on the diagonal)
#   - They wobble together a little (0.1 off-diagonal)
precision_matrix = np.array([[2.0, 0.1],
                             [0.1, 1.5]])

# The cost vector says: option A costs $0.60, B costs $0.40.
cost_vector = np.array([0.60, 0.40])
```

```python
# Solve it.
answer = Minimize(Variance(precision_matrix), cost_vector).value
print(answer)
```

You'll see something like:

```
[0.6522  0.9565]
```

Read that as: put **0.65 units of A** and **0.96 units of B** in
your portfolio. (A "unit" here is "however many contracts it takes
to spend $1.")

To leave the Python prompt:

```python
exit()
```

---

## Step 6 — Tweak one thing

Create a file called `config.json` in your project folder:

```json
{
  "runtime": {
    "seed": 7,
    "log_level": "INFO",
    "output_directory": "artifacts"
  },
  "optimization": {
    "alpha": 0.20,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
```

The only change: `alpha` went from `0.05` to `0.20`. Smaller alpha =
more cautious. Larger alpha = more aggressive.

Now run with the config:

```bash
convexfolio --config config.json --command reproduce-report
cat artifacts/report.json
```

Look at the `cfvar2_weights` and `cfvar3_weights` arrays. Compare
them to what you got before. Different alpha, different
recommendation.

> 🧪 **Experiment:** Try `alpha: 0.40` (almost the legal maximum).
> Notice how the weights get more extreme. Then try `alpha: 0.01`
> (very cautious). Notice how the weights spread out more evenly.

---

## What can go wrong

| Error | What it means | Fix |
|---|---|---|
| `command not found: convexfolio` | The sandbox isn't active or install failed. | Run `source .venv/bin/activate`, then `pip install -e '.[dev]'`. |
| `ModuleNotFoundError: No module named 'convexfolio'` | Same as above. | Re-activate and re-install. |
| `RuntimeError: Optimisation failed` | The math didn't converge. Usually because the inputs are extreme. | Try less extreme values; see [FAQ](faq.md). |
| `JSONDecodeError` | The config file isn't valid JSON. | Check the file for missing commas, unclosed brackets. |

---

## What now?

You now know the basics. Where to go next:

- **[FAQ](faq.md)** — Common questions.
- **[Glossary](glossary.md)** — All the technical terms.
- **[API Reference](api-reference.md)** — Every class and function,
  with examples.
- **[Architecture](architecture.md)** — How the pieces fit together.
