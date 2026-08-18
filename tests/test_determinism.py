from options.config import Experiment
from options.determinism import check


def test_pipeline_is_deterministic_given_same_seed() -> None:
    experiment = Experiment()
    report = check(experiment, repetitions=3)
    assert report.deterministic is True
