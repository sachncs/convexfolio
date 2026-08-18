import json
from pathlib import Path

import pytest

from options.config import load, validate


def test_load_defaults() -> None:
    experiment = load(None)
    assert experiment.optimization.alpha == 0.05


def test_validate_rejects_invalid_alpha(tmp_path: Path) -> None:
    experiment = load(None)
    raw_config = {
        "runtime": {
            "seed": experiment.runtime.seed,
            "log_level": experiment.runtime.log_level,
            "output_directory": experiment.runtime.output_directory,
        },
        "optimization": {
            "alpha": 0.6,
            "method": experiment.optimization.method,
            "enforce_nu_greater_than_six": (
                experiment.optimization.enforce_nu_greater_than_six
            ),
        },
    }
    config_file = tmp_path / "oop_bad_config.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    with pytest.raises(ValueError):
        validate(load(str(config_file)))


def test_load_json_default_key_alias(tmp_path: Path) -> None:
    raw_config = {
        "runtime": {"output_dir": "old_name_dir"},
        "optimization": {"alpha": 0.1},
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    experiment = load(str(config_file))
    assert experiment.runtime.output_directory == "old_name_dir"


def test_load_yaml(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    raw_config = """
runtime:
  seed: 42
  log_level: DEBUG
  output_directory: yaml_dir
optimization:
  alpha: 0.02
  method: numeric
  enforce_nu_greater_than_six: false
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(raw_config, encoding="utf-8")
    experiment = load(str(config_file))
    assert experiment.runtime.seed == 42
    assert experiment.runtime.log_level == "DEBUG"
    assert experiment.runtime.output_directory == "yaml_dir"
    assert experiment.optimization.alpha == pytest.approx(0.02)
    assert experiment.optimization.method == "numeric"
    assert experiment.optimization.enforce_nu_greater_than_six is False


def test_load_yml_extension(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    raw_config = "runtime:\n  seed: 5\n"
    config_file = tmp_path / "config.yml"
    config_file.write_text(raw_config, encoding="utf-8")
    experiment = load(str(config_file))
    assert experiment.runtime.seed == 5
