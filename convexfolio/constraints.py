"""Constraint builders for portfolio optimisation.

Each builder returns a constraint spec compatible with SciPy's
``scipy.optimize.minimize`` SLSQP solver, or a list of bounds for
``Minimize(Variance(Q), c)``-style closed-form solvers.

Three kinds:

* Bounds — ``(min, max)`` per weight (long-only, position limits).
* Equality — ``a @ x == b`` (the budget constraint).
* Inequality — ``a @ x <= b`` (sector caps, leverage cap).

SLSQP accepts a list of dicts; this module wraps the builders so
callers don't have to write the dict shape manually.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from convexfolio.types import FloatArray

SLSQPConstraint = dict[str, object]
ConstraintSpec = tuple[SLSQPConstraint, ...]


def budget(cost_vector: FloatArray) -> SLSQPConstraint:
    """Build the equality constraint ``x . v == 1``.

    Args:
        cost_vector: 1-D cost vector ``v``.

    Returns:
        A SciPy SLSQP constraint dict enforcing the budget.
    """
    return {
        "type": "eq",
        "fun": lambda x, v=cost_vector: float(np.dot(x, v) - 1.0),
    }


def bounds(min: float, max: float, n: int) -> Sequence[tuple[float, float]]:
    """Build per-instrument bounds ``min <= x[i] <= max``.

    Args:
        min: Lower bound (per weight).
        max: Upper bound (per weight).
        n: Number of instruments.

    Returns:
        A list of ``(min, max)`` tuples, length ``n``.
    """
    return [(float(min), float(max))] * int(n)


def inequality(
    coefficients: FloatArray, limit: float
) -> SLSQPConstraint:
    """Build the inequality constraint ``a . x <= limit``.

    Args:
        coefficients: 1-D coefficient vector ``a``.
        limit: Right-hand side.

    Returns:
        A SciPy SLSQP constraint dict.
    """
    return {
        "type": "ineq",
        "fun": lambda x, a=coefficients, b=limit: float(b - float(np.dot(x, a))),
    }


def merge(*groups: ConstraintSpec | Sequence[SLSQPConstraint]) -> ConstraintSpec:
    """Flatten multiple constraint groups into one tuple.

    Args:
        *groups: Tuples / lists of SLSQP constraint dicts.

    Returns:
        A single flat tuple of constraint dicts.
    """
    out: list[SLSQPConstraint] = []
    for g in groups:
        out.extend(g)
    return tuple(out)


def budget_with_extras(
    cost_vector: FloatArray, *extras: SLSQPConstraint
) -> ConstraintSpec:
    """Convenience: budget constraint plus any number of extras.

    Args:
        cost_vector: 1-D cost vector ``v``.
        *extras: Additional SLSQP constraint dicts.

    Returns:
        Tuple including the budget constraint and all extras.
    """
    return (budget(cost_vector), *extras)


def long_only_inequalities(n: int) -> ConstraintSpec:
    """Build inequality constraints enforcing ``x[i] >= 0`` for all i.

    SLSQP does not accept bounds directly with arbitrary other
    constraints; emitting ``-x[i] <= 0`` inequalities keeps the
    constraint representation uniform with the rest of this module.

    Args:
        n: Number of instruments.

    Returns:
        Tuple of ``n`` inequality constraints.
    """
    eyes = [np.eye(n, dtype=float)[i] for i in range(n)]
    return tuple(
        inequality(-eye, 0.0) for eye in eyes
    )


def long_only_bounds(n: int) -> Sequence[tuple[float, float]]:
    """Bounds tuple for ``long_only``-style closed-form solvers.

    Use this with solvers that accept SciPy's ``bounds`` parameter
    rather than SLSQP constraints.

    Args:
        n: Number of instruments.

    Returns:
        List of ``(0.0, inf)`` tuples.
    """
    return bounds(0.0, np.inf, n)
