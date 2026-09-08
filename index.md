---
layout: home
title: convexfolio
description: "Optimal Option Portfolios for Skew-Elliptical t Returns"
---

## Why Convexfolio

Given a handful of options to choose from, Convexfolio answers one question:

> *"How should I split my money between these options so my risk is as small as possible?"*

You feed in prices, expected payoffs, and a "how risky is each option" matrix. The
package returns the **weights** — the fraction of your budget that goes into each
option under the risk model you chose. It implements the math from
[arXiv:2601.07991v2](https://arxiv.org/abs/2601.07991v2); you don't need to read the
paper to use it.

<div class="lead-cards" style="margin-top:8px">

<div class="card">
  <span class="ico">📉</span>
  <h3>Variance minimisation</h3>
  <p>Find the weights that minimise how wildly your portfolio value bounces around.</p>
</div>

<div class="card">
  <span class="ico">⚡</span>
  <h3>CFVaR₂ — closed form</h3>
  <p>A faster, smarter risk measure with an exact formula and no iteration.</p>
</div>

<div class="card">
  <span class="ico">🎯</span>
  <h3>CFVaR₃ — numerical</h3>
  <p>A more accurate risk measure, solved numerically with scipy's SLSQP.</p>
</div>

<div class="card">
  <span class="ico">🔁</span>
  <h3>Deterministic by design</h3>
  <p>Same inputs always give byte-identical outputs — validated by a built-in determinism check.</p>
</div>

<div class="card">
  <span class="ico">💻</span>
  <h3>Terminal-first</h3>
  <p>Run reports from the command line, or import the solvers directly in Python.</p>
</div>

<div class="card">
  <span class="ico">⚙️</span>
  <h3>JSON / YAML config</h3>
  <p>Describe your constraints and settings in a plain text file and go.</p>
</div>

</div>

## Quick start

```bash
pip install convexfolio
convexfolio --command print-report
```

That prints a JSON report for a sample portfolio. Walk through every line, step by
step, in the [Getting Started guide]({{ site.baseurl }}/docs/getting-started/).

## Documentation

<div class="link-grid">

<a class="link-item" href="docs/getting-started/"><span><strong>Getting Started</strong><span>The beginner's walk-through — install, first run, first solver.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/api-reference/"><span><strong>API Reference</strong><span>Every public symbol, with examples.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/faq/"><span><strong>FAQ</strong><span>Common questions answered in plain English.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/glossary/"><span><strong>Glossary</strong><span>Every technical term, defined.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/architecture/"><span><strong>Architecture</strong><span>How the package is put together, for the curious.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/tutorials/backtesting/"><span><strong>Tutorial · Backtesting</strong><span>Multi-period rebalancing with transaction costs.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/tutorials/constraints/"><span><strong>Tutorial · Constraints</strong><span>Sector caps, position limits, leverage.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/tutorials/from-csv/"><span><strong>Tutorial · From CSV</strong><span>Load a real portfolio from a spreadsheet.</span></span><span class="arr">→</span></a>

<a class="link-item" href="docs/tutorials/visualisation/"><span><strong>Tutorial · Visualising</strong><span>Charts and plots for your portfolios.</span></span><span class="arr">→</span></a>

</div>

For operators and maintainers: [Deployment]({{ site.baseurl }}/docs/deployment/),
[Release process]({{ site.baseurl }}/docs/release/), [Fidelity report]({{ site.baseurl }}/docs/fidelity_report/),
[Research determination]({{ site.baseurl }}/docs/research_determination/),
[Mismatch report]({{ site.baseurl }}/docs/mismatch_report/).

> **Not investment advice.** Convexfolio is research software. The outputs are
> mathematical illustrations; verify them independently before any use.