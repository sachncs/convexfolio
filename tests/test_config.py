import json
from pathlib import Path

import pytest

from options.config import load
from options.config import validate


def test_load_defaults() -> None:
    experiment = load(None)
    assert experiment.optimization.alpha == 0.05


def test_validate_rejects_invalid_alpha(tmp_path: Path) -> None:
    experiment = load(None)
    raw_config = {
        "runtime": {
            "seed": experiment.runtime.seed,
            "log_level": experiment.runtime.log_level,
            "output_dir": experiment.runtime.output_dir,
        },
        "optimization": {
            "alpha": 0.6,
            "method": experiment.optimization.method,
            "enforce_nu_greater_than_six": experiment.optimization.enforce_nu_greater_than_six,
        },
    }
    config_file = tmp_path / "oop_bad_config.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    with pytest.raises(ValueError):
        validate(load(str(config_file)))
