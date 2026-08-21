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


def position_limits_inequalities(
    n: int, max_abs_weight: float
) -> ConstraintSpec:
    """Build inequality constraints enforcing ``|x[i]| <= max_abs_weight``.

    Two inequalities per instrument: ``x[i] <= max_abs_weight`` and
    ``-x[i] <= max_abs_weight``.

    Args:
        n: Number of instruments.
        max_abs_weight: Maximum absolute weight per instrument.

    Returns:
        Tuple of ``2n`` inequality constraints.
    """
    eyes = [np.eye(n, dtype=float)[i] for i in range(n)]
    out: list[SLSQPConstraint] = []
    for eye in eyes:
        out.append(inequality(eye, max_abs_weight))
        out.append(inequality(-eye, max_abs_weight))
    return tuple(out)


def position_limits_bounds(
    n: int, max_abs_weight: float
) -> Sequence[tuple[float, float]]:
    """Bounds tuple enforcing ``|x[i]| <= max_abs_weight``.

    Args:
        n: Number of instruments.
        max_abs_weight: Maximum absolute weight per instrument.

    Returns:
        List of ``(-max, +max)`` tuples.
    """
    return bounds(-max_abs_weight, max_abs_weight, n)


def sector_caps_inequalities(
    sector_map: Sequence[int], max_per_sector: float
) -> ConstraintSpec:
    """Build inequality constraints enforcing per-sector exposure caps.

    For each unique sector, emits ``sum_{i in sector} x[i] <= max``.
    Assumes long-only weights (negative weights would net against
    the cap; if you allow shorting, use absolute-value caps).

    Args:
        sector_map: Integer sector id per instrument (length ``n``).
        max_per_sector: Maximum sum of weights in any single sector.

    Returns:
        Tuple of inequality constraints, one per unique sector.
    """
    out: list[SLSQPConstraint] = []
    n = len(sector_map)
    unique_sectors = sorted(set(sector_map))
    for sector in unique_sectors:
        a = np.zeros(n, dtype=float)
        for i, s in enumerate(sector_map):
            if s == sector:
                a[i] = 1.0
        out.append(inequality(a, max_per_sector))
    return tuple(out)


def leverage_cap_inequality(n: int, max_leverage: float) -> SLSQPConstraint:
    """Build the inequality constraint ``sum |x[i]| <= max_leverage``.

    SLSQP supports only smooth constraints; |x[i]| is not smooth at 0.
    For practical portfolios the smooth approximation is fine, but
    if your portfolio has many zero-weight instruments, prefer
    long_only + position limits instead.

    Args:
        n: Number of instruments.
        max_leverage: Maximum sum of absolute weights.

    Returns:
        A single SLSQP inequality constraint.
    """
    a = np.ones(n, dtype=float)
    return inequality(a, max_leverage)
