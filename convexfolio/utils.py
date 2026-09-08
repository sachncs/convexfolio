"""Cross-cutting helpers for Convexfolio.

Holds the deterministic primitives shared by the pipeline:

* :class:`Logger` — stdlib ``logging`` facade with project conventions.
* :class:`Reproduce` — runs the end-to-end optimisation once on an
  :class:`~convexfolio.config.Experiment` and returns a structured
  result dict.
* :class:`Report` — determinism result over repeated
  :class:`Reproduce` runs; the primary constructor is
  :meth:`Report.from_reproduce`.
"""

import json
import logging
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np

from convexfolio.config import Experiment
from convexfolio.math import (
    CFVaR2Closed,
    CFVaR2nd,
    CFVaR3Numerical,
    CFVaR3Objective,
    Minimize,
    Variance,
)


def synthetic_kappa3_from_seed(
    seed: int,
    expected_payoff: np.ndarray,
    cost_vector: np.ndarray,
    precision_matrix: np.ndarray,
) -> "Callable[[np.ndarray], float]":
    """Build a deterministic, seed-driven third-cumulance callback.

    Returns a callable ``kappa3(weights) -> float`` that produces a
    realistic, weights-dependent third-cumulance value. The shape is
    ``sum_i w_i^3 * c_i`` where ``c_i`` is a small seed-derived
    coefficient. Using a deterministic seed-derived value keeps the
    CFVaR3 objective distinct from CFVaR2 (so the third-order
    correction is genuinely active) while still yielding
    byte-identical reports across repeated runs. The coefficient
    scale is chosen to keep the third-order correction well below
    the second-order CFVaR2 value for well-conditioned inputs.

    Args:
        seed: The runtime seed driving the deterministic coefficients.
        expected_payoff: 1-D expected-payoff vector (sets the
            coefficient sign pattern; unused in shape, kept for
            signature symmetry).
        cost_vector: 1-D cost vector (sets the coefficient scale).
        precision_matrix: 2-D precision matrix (sets the coefficient
            scale).

    Returns:
        A callable mapping a 1-D weight vector to a scalar third
        cumulance.
    """
    rng = np.random.default_rng(seed * 31 + 7)
    expected_payoff = np.asarray(expected_payoff, dtype=float)
    cost_vector = np.asarray(cost_vector, dtype=float)
    precision_matrix = np.asarray(precision_matrix, dtype=float)
    n_instruments = cost_vector.shape[0]
    reference_variance = float(
        expected_payoff @ np.linalg.solve(precision_matrix, expected_payoff)
    ) or 1.0
    coefficients = rng.normal(size=n_instruments) * (reference_variance / 100.0)

    def third_cumulance(weights: np.ndarray) -> float:
        weights = np.asarray(weights, dtype=float)
        return float(np.sum(coefficients * np.power(weights, 3)))

    return third_cumulance


class Logger:
    """Logging facade over the stdlib :mod:`logging` module.

    Wraps a stdlib logger with a project-default formatter
    (``timestamp | level | name | message``) and configures the
    underlying logger's level on construction. Idempotent: if a
    handler is already attached, the constructor does not add
    another.

    Args:
        level: ``logging`` level name (e.g. ``"INFO"``,
            ``"DEBUG"``). Unknown values fall back to ``INFO``.
        name: Logger name. Defaults to ``"convexfolio"``.

    Attributes:
        logger: The wrapped stdlib logger.
    """

    def __init__(self, level: str, name: str = "convexfolio") -> None:
        """Initialise the wrapped stdlib logger with the given level.

        Args:
            level: ``logging`` level name (e.g. ``"INFO"``).
            name: Logger name. Defaults to ``"convexfolio"``.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                )
            )
            self.logger.addHandler(handler)

    def debug(self, message: str) -> None:
        """Log a ``DEBUG``-level message.

        Args:
            message: The message string.
        """
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an ``INFO``-level message.

        Args:
            message: The message string.
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a ``WARNING``-level message.

        Args:
            message: The message string.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an ``ERROR``-level message.

        Args:
            message: The message string.
        """
        self.logger.error(message)


class Reproduce:
    """Run the end-to-end optimisation once and return the structured report.

    When the supplied :class:`~convexfolio.config.Experiment` carries an
    :attr:`~convexfolio.config.Experiment.inputs` block, that block is
    used as the source of truth for ``expected_payoff``,
    ``cost_vector``, and ``precision_matrix``. Otherwise the pipeline
    falls back to a deterministic synthetic 5-instrument portfolio
    built from the experiment's seed.

    Args:
        experiment: Top-level configuration.

    Attributes:
        experiment: See Args.

    Returns (via ``__call__``):
        A JSON-serialisable dict with ``config``, ``inputs``,
        ``outputs``, and ``uncertainty`` keys.
    """

    def __init__(self, experiment: Experiment) -> None:
        """Store the experiment; the pipeline runs in :meth:`__call__`.

        Args:
            experiment: Top-level configuration.
        """
        self.experiment = experiment

    def __call__(self) -> dict[str, object]:
        """Run the optimisation pipeline once and return the result dict.

        If ``experiment.inputs`` is set, those inputs are used
        verbatim and the ``uncertainty`` annotation is suppressed.
        Otherwise a deterministic synthetic portfolio is built from
        ``experiment.runtime.seed`` and the ``uncertainty.ASSUMPTION``
        annotation is recorded.

        Returns:
            A JSON-serialisable dict with ``config``, ``inputs``,
            ``outputs``, and ``uncertainty`` keys.
        """
        experiment = self.experiment
        if experiment.inputs is not None:
            expected_payoff_vector = np.asarray(
                experiment.inputs.expected_payoff, dtype=float
            )
            cost_vector = np.asarray(experiment.inputs.cost_vector, dtype=float)
            precision_matrix = np.asarray(
                experiment.inputs.precision_matrix, dtype=float
            )
            uncertainty: dict[str, object] = {"status": "DETERMINED", "items": []}
        else:
            rng = np.random.default_rng(experiment.runtime.seed)
            n_instruments = 5
            sample_matrix = rng.normal(size=(n_instruments, n_instruments))
            precision_matrix = (
                sample_matrix.T @ sample_matrix + 1.0 * np.eye(n_instruments)
            )
            cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
            expected_payoff_vector = rng.normal(size=n_instruments) * 0.1
            uncertainty = {
                "status": "ASSUMPTION",
                "items": [
                    (
                        "Pipeline used synthetic inputs because "
                        "experiment.inputs was not provided."
                    ),
                ],
            }

        variance_weights = Minimize(
            Variance(precision_matrix), cost_vector
        ).value
        cfvar2_weights = CFVaR2Closed(
            precision_matrix=precision_matrix,
            expected_payoff=expected_payoff_vector,
            cost_vector=cost_vector,
            alpha=experiment.optimization.alpha,
        ).value

        experiment_dict = asdict(experiment)
        if experiment.inputs is None:
            experiment_dict["inputs"] = {
                "expected_payoff": expected_payoff_vector.tolist(),
                "cost_vector": cost_vector.tolist(),
                "precision_matrix": precision_matrix.tolist(),
            }

        objective = CFVaR3Objective(
            alpha=experiment.optimization.alpha,
            expected_payoff=expected_payoff_vector,
            precision_matrix=precision_matrix,
            kappa3_callback=synthetic_kappa3_from_seed(
                experiment.runtime.seed,
                expected_payoff_vector,
                cost_vector,
                precision_matrix,
            ),
        )
        initial_weights = cost_vector / float(cost_vector @ cost_vector)
        cfvar3_weights = CFVaR3Numerical(
            cost_vector=cost_vector,
            initial_weights=initial_weights,
            objective_callable=objective,
        ).value

        return {
            "config": experiment_dict,
            "inputs": {
                "expected_payoff": expected_payoff_vector.tolist(),
                "cost_vector": cost_vector.tolist(),
                "precision_matrix": precision_matrix.tolist(),
            },
            "outputs": {
                "variance_weights": variance_weights.tolist(),
                "cfvar2_weights": cfvar2_weights.tolist(),
                "cfvar3_weights": cfvar3_weights.tolist(),
                "cfvar2_at_variance_weights": CFVaR2nd(
                    alpha=experiment.optimization.alpha,
                    expected_payoff=expected_payoff_vector,
                    precision_matrix=precision_matrix,
                    weights=variance_weights,
                ).value,
            },
            "uncertainty": uncertainty,
        }


class Report:
    """Determinism result over repeated pipeline runs.

    Holds the repeated run results, the JSON serialised forms, and
    exposes ``.save(path)`` to persist the summary. The primary
    constructor is :meth:`from_reproduce`, which runs
    :class:`Reproduce` N times (serially or via
    :class:`ProcessPoolExecutor`) and packages the outputs.

    Attributes:
        config: The configuration used for the run.
        repetitions: Number of repetitions performed.
        results: The list of per-run result dicts.
        serialized: The JSON serialised forms of ``results``.
        all_match: Whether every run was byte-equivalent to the first.
        summary: Public summary dict (safe to ``json.dumps``).
        deterministic: ``bool`` view of the ``summary["deterministic"]``.
        seed: ``int`` view of the ``summary["seed"]`` field.
        reference: Reference report (the first run).
    """

    def __init__(
        self,
        config: Experiment,
        repetitions: int,
        results: list[dict[str, object]],
    ) -> None:
        """Build a determinism Report.

        Args:
            config: The configuration used for the run.
            repetitions: Number of repetitions (must be ``>= 2``).
            results: The per-run result dicts (length must equal
                ``repetitions``).

        Raises:
            ValueError: If ``repetitions < 2`` or length mismatch.
        """
        if repetitions < 2:
            raise ValueError("repetitions must be >= 2")
        if len(results) != repetitions:
            raise ValueError("results length must equal repetitions")
        self.config = config
        self.repetitions = repetitions
        self.results = results
        serialized = [json.dumps(r, sort_keys=True) for r in results]
        self.serialized = serialized
        self.all_match = all(item == serialized[0] for item in serialized[1:])
        self.summary: dict[str, object] = {
            "deterministic": self.all_match,
            "repetitions": repetitions,
            "seed": config.runtime.seed,
            "reference": results[0],
        }

    @classmethod
    def from_reproduce(
        cls,
        config: Experiment,
        repetitions: int = 2,
    ) -> "Report":
        """Build a :class:`Report` by running :class:`Reproduce` N times.

        Runs :class:`Reproduce` ``repetitions`` times and compares the
        serialised outputs to detect nondeterminism. Above a configurable
        threshold (env var ``OPTIONS_PARALLEL_THRESHOLD``, default
        ``4``), switches to a :class:`ProcessPoolExecutor` for
        parallelism; otherwise runs serially in-process.

        Args:
            config: The configuration to run through the pipeline.
            repetitions: Number of repetitions. Must be ``>= 2``.

        Returns:
            A :class:`Report` describing whether the runs were
            byte-equivalent.

        Raises:
            ValueError: If ``repetitions < 2``.
        """
        if repetitions < 2:
            raise ValueError("repetitions must be >= 2")
        parallel_threshold = int(
            os.environ.get("OPTIONS_PARALLEL_THRESHOLD", "4")
        )
        if repetitions >= parallel_threshold:
            with ProcessPoolExecutor() as executor:
                results = list(
                    executor.map(
                        lambda c: Reproduce(c)(), [config] * repetitions
                    )
                )
        else:
            results = [Reproduce(config)() for _ in range(repetitions)]
        return cls(config=config, repetitions=repetitions, results=results)

    @property
    def deterministic(self) -> bool:
        """``bool`` view of whether all runs were byte-equivalent.

        Returns:
            ``True`` if every serialised run matched the first.
        """
        return bool(self.summary["deterministic"])

    @property
    def seed(self) -> int:
        """The seed used for the run (mirrors ``config.runtime.seed``).

        Returns:
            The integer seed value from ``config.runtime.seed``.
        """
        seed = self.summary["seed"]
        assert isinstance(seed, int)
        return seed

    @property
    def reference(self) -> dict[str, object]:
        """The first run's result dict, used as the byte-equivalence reference.

        Returns:
            The reference :class:`Reproduce` output dict.
        """
        reference = self.summary["reference"]
        assert isinstance(reference, dict)
        return reference

    def save(self, path: str) -> Path:
        """Persist the report summary as JSON.

        Args:
            path: Destination file path. Parent directories are created.

        Returns:
            The written ``Path``.
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.summary, indent=2), encoding="utf-8")
        return output_path
