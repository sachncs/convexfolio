"""Production execution pipeline for reproducible optimization runs."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from options.config import ExperimentConfig
from options.optimization import cfvar3_objective
from options.optimization import solve_cfvar2_closed_form
from options.optimization import solve_cfvar3_numerical
from options.optimization import solve_variance_minimization
from options.risk import cfvar2


def run_reproduction(experiment: ExperimentConfig) -> dict[str, object]:
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

    variance_solution = solve_variance_minimization(cost_vector, precision_matrix)
    cfvar2_solution = solve_cfvar2_closed_form(
        q_matrix=precision_matrix,
        u=expected_payoff_vector,
        v=cost_vector,
        alpha=experiment.optimization.alpha,
    )

    kappa3_callback = lambda x: 0.0
    objective = cfvar3_objective(
        alpha=experiment.optimization.alpha,
        u=expected_payoff_vector,
        q_matrix=precision_matrix,
        kappa3_callback=kappa3_callback,
    )
    initial_weights = np.ones(n_instruments) / np.sum(cost_vector)
    cfvar3_solution = solve_cfvar3_numerical(
        v=cost_vector,
        initial_x=initial_weights,
        objective_callable=objective,
    )

    return {
        "config": asdict(experiment),
        "inputs": {
            "u": expected_payoff_vector.tolist(),
            "v": cost_vector.tolist(),
            "q_matrix": precision_matrix.tolist(),
        },
        "outputs": {
            "variance_solution": variance_solution.tolist(),
            "cfvar2_solution": cfvar2_solution.tolist(),
            "cfvar3_solution": cfvar3_solution.tolist(),
            "cfvar2_at_variance_solution": cfvar2(
                experiment.optimization.alpha,
                expected_payoff_vector,
                precision_matrix,
                variance_solution,
            ),
        },
        "uncertainty": {
            "status": "ASSUMPTION",
            "items": [
                "Pipeline demo uses synthetic inputs; real-market replication requires data-specific integration.",
            ],
        },
    }


def save_report(report: dict[str, object], output_directory: str) -> Path:
    """Persists JSON report for reproducibility and downstream systems."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / "reproduction_report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_file
