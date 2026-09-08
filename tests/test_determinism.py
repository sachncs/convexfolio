"""Tests for :meth:`Report.from_reproduce` determinism orchestration."""

import json

import numpy as np
import pytest

from convexfolio.config import Experiment, PortfolioInputs
from convexfolio.utils import Report, Reproduce


def test_pipeline_is_deterministic_given_same_seed() -> None:
    """Three repeated runs produce byte-equivalent reports."""
    experiment = Experiment()
    report = Report.from_reproduce(experiment, repetitions=3)
    assert report.deterministic is True
    assert report.repetitions == 3
    assert len(report.results) == 3
    assert report.all_match is True


def test_report_from_reproduce_serialises_summary() -> None:
    """The summary dict round-trips through json.dumps."""
    experiment = Experiment()
    report = Report.from_reproduce(experiment, repetitions=2)
    json.dumps(report.summary)  # must not raise
    assert "deterministic" in report.summary
    assert "seed" in report.summary
    assert "repetitions" in report.summary


def test_report_from_reproduce_rejects_single_repetition() -> None:
    """ValueError raised when repetitions < 2."""
    experiment = Experiment()
    with pytest.raises(ValueError, match="repetitions must be >= 2"):
        Report.from_reproduce(experiment, repetitions=1)


def test_reproduce_honours_user_inputs() -> None:
    """User-supplied Experiment.inputs round-trip through Reproduce."""
    expected_payoff = np.array([0.05, 0.10, 0.07])
    cost_vector = np.array([1.0, 2.0, 1.5])
    precision_matrix = np.eye(3) * 2.0
    experiment = Experiment(
        inputs=PortfolioInputs(
            expected_payoff=expected_payoff,
            cost_vector=cost_vector,
            precision_matrix=precision_matrix,
        )
    )
    result = Reproduce(experiment)()
    assert result["inputs"]["expected_payoff"] == pytest.approx(
        expected_payoff.tolist()
    )
    assert result["inputs"]["cost_vector"] == pytest.approx(cost_vector.tolist())
    assert np.allclose(
        np.asarray(result["inputs"]["precision_matrix"]),
        precision_matrix,
    )
    assert result["uncertainty"]["status"] == "DETERMINED"


def test_cfvar3_differs_from_cfvar2_in_synthetic_path() -> None:
    """The synthetic-data pipeline yields cfvar3 != cfvar2."""
    experiment = Experiment()
    result = Reproduce(experiment)()
    cfvar2_weights = np.asarray(result["outputs"]["cfvar2_weights"])
    cfvar3_weights = np.asarray(result["outputs"]["cfvar3_weights"])
    assert np.max(np.abs(cfvar3_weights - cfvar2_weights)) > 1e-8
