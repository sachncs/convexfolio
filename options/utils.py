"""Cross-cutting helpers for the options package.

Holds the deterministic primitives that are shared by ``determinism`` and
``pipeline``: Logger for output, Report for determinism results, and
``reproduce`` for the single-run pipeline execution.
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np

from options.config import Experiment
from options.math import Greeks
from options.math import Linearize
from options.math import Reconstruct
from options.math import Risk
from options.math import Solve
from options.math import ThirdOrderObjective


class Logger:
    """Logging facade over the stdlib ``logging`` module.

    Single concrete class; no subclasses, no polymorphism.
    """

    def __init__(self, level: str, name: str = "options") -> None:
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


def reproduce(experiment: Experiment) -> dict[str, object]:
    """Runs the end-to-end optimization once and returns structured outputs.

    Uses synthetic matrices as a self-contained smoke pipeline. External data
    ingestion is project-dependent and plugin users can replace this stage.
    """
    rng = np.random.default_rng(experiment.runtime.seed)
    n_instruments = 5
    sample_matrix = rng.normal(size=(n_instruments, n_instruments))
    precision_matrix = (
        sample_matrix.T @ sample_matrix + 0.5 * np.eye(n_instruments)
    )
    cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
    expected_payoff_vector = rng.normal(size=n_instruments)

    variance_solution = Solve(
        kind="variance",
        cost_vector=cost_vector,
        precision_matrix=precision_matrix,
    ).value
    cfvar2_solution = Solve(
        kind="cfvar2",
        precision_matrix=precision_matrix,
        expected_payoff=expected_payoff_vector,
        cost_vector=cost_vector,
        alpha=experiment.optimization.alpha,
    ).value

    risk = Risk(
        alpha=experiment.optimization.alpha,
        expected_payoff=expected_payoff_vector,
        precision_matrix=precision_matrix,
    )
    objective = ThirdOrderObjective(
        alpha=experiment.optimization.alpha,
        expected_payoff=expected_payoff_vector,
        precision_matrix=precision_matrix,
        kappa3_callback=lambda weights: 0.0,
    )
    initial_weights = np.ones(n_instruments) / np.sum(cost_vector)
    cfvar3_solution = Solve(
        kind="cfvar3",
        cost_vector=cost_vector,
        initial_weights=initial_weights,
        objective_callable=objective,
    ).value

    return {
        "config": asdict(experiment),
        "inputs": {
            "u": expected_payoff_vector.tolist(),
            "v": cost_vector.tolist(),
            "qmatrix": precision_matrix.tolist(),
        },
        "outputs": {
            "variance_solution": variance_solution.tolist(),
            "cfvar2_solution": cfvar2_solution.tolist(),
            "cfvar3_solution": cfvar3_solution.tolist(),
            "cfvar2_at_variance_solution": risk.second(variance_solution),
        },
        "uncertainty": {
            "status": "ASSUMPTION",
            "items": [
                "Pipeline demo uses synthetic inputs; real-market replication requires data-specific integration.",
            ],
        },
    }


class Report:
    """Standard deterministic determinism result.

    Holds repeated pipeline runs and exposes ``.save(path)`` to persist the
    summary as JSON. Used by both ``determinism`` and ``pipeline``.
    """

    def __init__(
        self,
        config: Experiment,
        repetitions: int,
        results: list[dict[str, object]],
    ) -> None:
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

    @property
    def deterministic(self) -> bool:
        return bool(self.summary["deterministic"])

    @property
    def seed(self) -> int:
        return int(self.summary["seed"])

    @property
    def reference(self) -> dict[str, object]:
        return self.summary["reference"]

    def save(self, path: str) -> Path:
        """Persist the report summary as JSON. Returns the written path."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.summary, indent=2), encoding="utf-8"
        )
        return output_path
