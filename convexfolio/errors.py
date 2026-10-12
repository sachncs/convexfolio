"""Public exception types for validated Convexfolio operations."""


class ConvexfolioError(Exception):
    """Base class for expected Convexfolio failures."""


class ValidationError(ConvexfolioError, ValueError):
    """Raised when caller-provided data violates a domain contract."""


class InfeasibleProblemError(ConvexfolioError, ValueError):
    """Raised when no portfolio satisfies the configured constraints."""


class SolverFailureError(ConvexfolioError, RuntimeError):
    """Raised when a numerical solver cannot produce a valid result."""


__all__ = [
    "ConvexfolioError",
    "InfeasibleProblemError",
    "SolverFailureError",
    "ValidationError",
]
