"""Production execution pipeline for reproducible optimization runs."""

from dataclasses import asdict
from pathlib import Path

import numpy as np

from options.config import Experiment
from options.math import Objective
from options.math import Risk
from options.math import minimize_variance
from options.math import solve_cfvar2_closed_form
from options.math import solve_cfvar3_numerical
from options.math import third_order_objective


def reproduce(experiment: Experiment) -> dict[str, object]:
    """Runs end-to-end optimization and returns structured outputs.

    Uses synthetic matrices as a self-contained production smoke pipeline.
    External data ingestion is project-dependent and plugin users can replace this stage.
    """
    rng = np.random.default_rng(experiment.runtime.seed)
    n_instruments = 5
    sample_matrix = rng.normal(size=(n_instruments, n_instruments))
    precision_matrix = (
        sample_matrix.T @ sample_matrix + 0.5 * np.eye(n_instruments)
    )
    cost_vector = np.abs(rng.normal(size=n_instruments)) + 0.1
    expected_payoff_vector = rng.normal(size=n_instruments)

    variance_solution = minimize_variance(cost_vector, precision_matrix)
    cfvar2_solution = solve_cfvar2_closed_form(
        precision_matrix=precision_matrix,
        expected_payoff=expected_payoff_vector,
        cost_vector=cost_vector,
        alpha=experiment.optimization.alpha,
    )

    risk = Risk(
        alpha=experiment.optimization.alpha,
        expected_payoff=expected_payoff_vector,
        precision_matrix=precision_matrix,
    )
    kappa3_callback = lambda weights: 0.0
    objective = Objective(
        third_order_objective,
        alpha=experiment.optimization.alpha,
        expected_payoff=expected_payoff_vector,
        precision_matrix=precision_matrix,
        kappa3_callback=kappa3_callback,
    )
    initial_weights = np.ones(n_instruments) / np.sum(cost_vector)
    cfvar3_solution = solve_cfvar3_numerical(
        cost_vector=cost_vector,
        initial_weights=initial_weights,
        objective_callable=objective,
    )

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


def run_and_save(experiment: Experiment, output_dir: str) -> Path:
    """Runs determinism check and saves the Report summary as JSON."""
    from options.determinism import check
    report = check(experiment, repetitions=3)
    target = Path(output_dir) / "report.json"
    return report.save(str(target))
