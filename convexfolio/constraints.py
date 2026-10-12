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

from collections.abc import Callable, Sequence
from functools import partial

import numpy as np

from convexfolio.errors import ValidationError
from convexfolio.types import FloatArray
from convexfolio.validation import copy_float_vector

SLSQPLambda = Callable[[np.ndarray], float]
SLSQPConstraint = dict[str, str | SLSQPLambda]
ConstraintSpec = tuple[SLSQPConstraint, ...]


def fun_of(constraint: SLSQPConstraint) -> SLSQPLambda:
    """Type-narrowed accessor for the ``fun`` callable in a constraint.

    Args:
        constraint: An SLSQP constraint dict produced by :func:`budget`,
            :func:`inequality`, etc.

    Returns:
        The ``fun`` callable, narrowed to :data:`SLSQPLambda`.

    Raises:
        TypeError: If ``constraint["fun"]`` is not callable.
    """
    f = constraint["fun"]
    if not callable(f):
        raise TypeError(f"constraint['fun'] must be callable, got {type(f).__name__}")
    return f


def budget_residual(cost_vector: FloatArray, x: np.ndarray) -> float:
    """Evaluate the budget residual ``x . v - 1``.

    Args:
        cost_vector: 1-D cost vector ``v``.
        x: 1-D weight vector.

    Returns:
        The signed residual; positive means over-budget, negative means
        under-budget.
    """
    weights = np.asarray(x, dtype=float)
    if weights.ndim != 1 or weights.shape != cost_vector.shape:
        raise ValidationError("weights and cost_vector must have matching shapes")
    return float(np.dot(weights, cost_vector) - 1.0)


def budget(cost_vector: FloatArray) -> SLSQPConstraint:
    """Build the equality constraint ``x . v == 1``.

    Args:
        cost_vector: 1-D cost vector ``v``.

    Returns:
        A SciPy SLSQP constraint dict enforcing the budget.
    """
    validated_costs = copy_float_vector(cost_vector, "cost_vector")
    if np.any(validated_costs <= 0.0):
        raise ValidationError("cost_vector must contain only positive values")
    bound_fun: SLSQPLambda = partial(budget_residual, validated_costs)
    return {"type": "eq", "fun": bound_fun}


def bounds(min: float, max: float, n: int) -> Sequence[tuple[float, float]]:
    """Build per-instrument bounds ``min <= x[i] <= max``.

    Args:
        min: Lower bound (per weight).
        max: Upper bound (per weight).
        n: Number of instruments.

    Returns:
        A list of ``(min, max)`` tuples, length ``n``.
    """
    if n < 0:
        raise ValidationError("n must be non-negative")
    if np.isnan(min) or np.isnan(max) or min > max:
        raise ValidationError("bounds must not contain NaN and min must not exceed max")
    return [(float(min), float(max))] * int(n)


def inequality_residual(coefficients: FloatArray, limit: float, x: np.ndarray) -> float:
    """Evaluate the inequality residual ``limit - a . x``.

    Args:
        coefficients: 1-D coefficient vector ``a``.
        limit: Right-hand side.
        x: 1-D weight vector.

    Returns:
        Slack to the constraint; positive means feasible, negative
        means violated.
    """
    weights = np.asarray(x, dtype=float)
    if weights.ndim != 1 or weights.shape != coefficients.shape:
        raise ValidationError("weights and coefficients must have matching shapes")
    return float(limit - float(np.dot(weights, coefficients)))


def inequality(coefficients: FloatArray, limit: float) -> SLSQPConstraint:
    """Build the inequality constraint ``a . x <= limit``.

    Args:
        coefficients: 1-D coefficient vector ``a``.
        limit: Right-hand side.

    Returns:
        A SciPy SLSQP constraint dict.
    """
    validated_coefficients = copy_float_vector(coefficients, "coefficients")
    if not np.isfinite(limit):
        raise ValidationError("constraint limit must be finite")
    ineq_fun: SLSQPLambda = partial(
        inequality_residual, validated_coefficients, float(limit)
    )
    return {"type": "ineq", "fun": ineq_fun}


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
    if n < 0:
        raise ValidationError("n must be non-negative")
    eyes = [np.eye(n, dtype=float)[i] for i in range(n)]
    return tuple(inequality(-eye, 0.0) for eye in eyes)


def position_limits_inequalities(n: int, max_abs_weight: float) -> ConstraintSpec:
    """Build inequality constraints enforcing ``|x[i]| <= max_abs_weight``.

    Two inequalities per instrument: ``x[i] <= max_abs_weight`` and
    ``-x[i] <= max_abs_weight``.

    Args:
        n: Number of instruments.
        max_abs_weight: Maximum absolute weight per instrument.

    Returns:
        Tuple of ``2n`` inequality constraints.
    """
    if n < 0:
        raise ValidationError("n must be non-negative")
    if not np.isfinite(max_abs_weight) or max_abs_weight < 0.0:
        raise ValidationError("max_abs_weight must be finite and non-negative")
    eyes = [np.eye(n, dtype=float)[i] for i in range(n)]
    out: list[SLSQPConstraint] = []
    for eye in eyes:
        out.append(inequality(eye, max_abs_weight))
        out.append(inequality(-eye, max_abs_weight))
    return tuple(out)


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
    if not np.isfinite(max_per_sector):
        raise ValidationError("max_per_sector must be finite")
    instrument_count = len(sector_map)
    unique_sectors = sorted(set(sector_map))
    for sector in unique_sectors:
        a = np.zeros(instrument_count, dtype=float)
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
    if n < 0:
        raise ValidationError("n must be non-negative")
    if not np.isfinite(max_leverage) or max_leverage < 0.0:
        raise ValidationError("max_leverage must be finite and non-negative")

    def absolute_leverage_residual(x: np.ndarray) -> float:
        weights = np.asarray(x, dtype=float)
        if weights.ndim != 1 or weights.shape != (n,):
            raise ValidationError("weights must match the requested instrument count")
        return float(max_leverage - np.sum(np.abs(weights)))

    return {"type": "ineq", "fun": absolute_leverage_residual}
