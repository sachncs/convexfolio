from oop.config import ExperimentConfig
from oop.determinism import deterministic_report


def test_pipeline_is_deterministic_given_same_seed() -> None:
    experiment = ExperimentConfig()
    determinism_summary = deterministic_report(
        config=experiment, repetitions=3
    )
    assert determinism_summary["deterministic"] is True
