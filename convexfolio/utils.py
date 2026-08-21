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


class Logger:
    """Logging facade over the stdlib ``logging`` module.

    Single concrete class; no subclasses, no polymorphism.

    Attributes:
        logger: The wrapped stdlib logger.
    """

    def __init__(self, level: str, name: str = "convexfolio") -> None:
        """Initialise the wrapped stdlib logger with the given level.

        Args:
            level: ``logging`` level name (e.g. ``"INFO"``).
            name: Logger name. Defaults to ``"options"``.
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
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)


class Reproduce:
    """Run the end-to-end optimisation once and return the structured report.

    Uses synthetic matrices as a self-contained smoke pipeline. External
    data ingestion is project-dependent; downstream users can replace
    this stage by composing their own :class:`Reproduce` subclass or by
    composing :class:`Reproduce` with a custom solver.

    Args:
        experiment: Top-level configuration.

    Attributes:
        experiment: See Args.

    Returns (via ``__call__``):
        A JSON-serialisable dict with ``config``, ``inputs``,
        ``outputs``, and ``uncertainty`` keys.
    """

    def __init__(self, experiment: Experiment) -> None:
        self.experiment = experiment

    def __call__(self) -> dict[str, object]:
        experiment = self.experiment
        rng = np.random.default_rng(experiment.runtime.seed)
        n_instruments = 5
        sample_matrix = rng.normal(size=(n_instruments, n_instruments))
        precision_matrix = (
            sample_matrix.T @ sample_matrix + 0.5 * np.eye(n_instruments)
        )
        cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
        expected_payoff_vector = rng.normal(size=n_instruments)

        variance_weights = Minimize(
            Variance(precision_matrix), cost_vector
        ).value
        cfvar2_weights = CFVaR2Closed(
            precision_matrix=precision_matrix,
            expected_payoff=expected_payoff_vector,
            cost_vector=cost_vector,
            alpha=experiment.optimization.alpha,
        ).value
        # Persist the synthetic inputs on the returned config dict so
        # the `inputs` round-trips correctly through JSON.
        experiment_dict = asdict(experiment)
        experiment_dict["inputs"] = {
            "expected_payoff": expected_payoff_vector.tolist(),
            "cost_vector": cost_vector.tolist(),
            "precision_matrix": precision_matrix.tolist(),
        }

        objective = CFVaR3Objective(
            alpha=experiment.optimization.alpha,
            expected_payoff=expected_payoff_vector,
            precision_matrix=precision_matrix,
            kappa3_callback=lambda weights: 0.0,
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
                "u": expected_payoff_vector.tolist(),
                "v": cost_vector.tolist(),
                "qmatrix": precision_matrix.tolist(),
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
            "uncertainty": {
                "status": "ASSUMPTION",
                "items": [
                    (
                        "Pipeline demo uses synthetic inputs; real-market "
                        "replication requires data-specific integration."
                    ),
                ],
            },
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
        return bool(self.summary["deterministic"])

    @property
    def seed(self) -> int:
        seed = self.summary["seed"]
        assert isinstance(seed, int)
        return seed

    @property
    def reference(self) -> dict[str, object]:
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
