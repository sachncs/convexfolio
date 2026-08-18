from options.config import ExperimentConfig
from options.determinism import deterministic_report


def test_pipeline_is_deterministic_given_same_seed() -> None:
    config = ExperimentConfig()
    summary = deterministic_report(config=config, repetitions=3)
    assert summary["deterministic"] is True
