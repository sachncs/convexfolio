"""Tests for :meth:`Report.from_reproduce` determinism orchestration."""

from convexfolio.config import Experiment
from convexfolio.utils import Report


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
    import json

    experiment = Experiment()
    report = Report.from_reproduce(experiment, repetitions=2)
    json.dumps(report.summary)  # must not raise
    assert "deterministic" in report.summary
    assert "seed" in report.summary
    assert "repetitions" in report.summary


def test_report_from_reproduce_rejects_single_repetition() -> None:
    """ValueError raised when repetitions < 2."""
    import pytest

    experiment = Experiment()
    with pytest.raises(ValueError, match="repetitions must be >= 2"):
        Report.from_reproduce(experiment, repetitions=1)
