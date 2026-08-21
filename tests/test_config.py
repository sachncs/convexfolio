"""Tests for the LoadConfig and Validate composition classes."""

import json
from pathlib import Path

import pytest

from convexfolio.config import LoadConfig, Validate


def test_load_config_defaults() -> None:
    """LoadConfig(None)() returns a default Experiment."""
    experiment = LoadConfig(None)()
    assert experiment.optimization.alpha == 0.05


def test_validate_rejects_invalid_alpha(tmp_path: Path) -> None:
    """Validate raises ValueError on out-of-bounds alpha."""
    experiment = LoadConfig(None)()
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
        LoadConfig(str(config_file))()


def test_validate_alpha_zero_and_one_rejected(tmp_path: Path) -> None:
    """Alpha at the boundary (0 or 0.5) is rejected."""
    experiment = LoadConfig(None)()
    raw_config = {
        "runtime": {
            "seed": experiment.runtime.seed,
            "log_level": experiment.runtime.log_level,
            "output_directory": experiment.runtime.output_directory,
        },
        "optimization": {
            "alpha": 0.0,
            "method": experiment.optimization.method,
            "enforce_nu_greater_than_six": (
                experiment.optimization.enforce_nu_greater_than_six
            ),
        },
    }
    config_file = tmp_path / "alpha_zero.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    with pytest.raises(ValueError):
        LoadConfig(str(config_file))()


def test_load_config_json_default_key_alias(tmp_path: Path) -> None:
    """Legacy 'output_dir' key is mapped to 'output_directory'."""
    raw_config = {
        "runtime": {"output_dir": "old_name_dir"},
        "optimization": {"alpha": 0.1},
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    experiment = LoadConfig(str(config_file))()
    assert experiment.runtime.output_directory == "old_name_dir"


def test_load_config_yaml(tmp_path: Path) -> None:
    """YAML configs load with all fields correctly typed."""
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
    experiment = LoadConfig(str(config_file))()
    assert experiment.runtime.seed == 42
    assert experiment.runtime.log_level == "DEBUG"
    assert experiment.runtime.output_directory == "yaml_dir"
    assert experiment.optimization.alpha == pytest.approx(0.02)
    assert experiment.optimization.method == "numeric"
    assert experiment.optimization.enforce_nu_greater_than_six is False


def test_load_config_yml_extension(tmp_path: Path) -> None:
    """.yml files are dispatched to the YAML loader."""
    raw_config = "runtime:\n  seed: 5\n"
    config_file = tmp_path / "config.yml"
    config_file.write_text(raw_config, encoding="utf-8")
    experiment = LoadConfig(str(config_file))()
    assert experiment.runtime.seed == 5


def test_validate_accepts_default_experiment() -> None:
    """Validate(default Experiment) does not raise."""
    experiment = LoadConfig(None)()
    Validate(experiment)


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        LoadConfig(str(tmp_path / "nonexistent.json"))()


def test_load_config_invalid_json_raises(tmp_path: Path) -> None:
    """Invalid JSON raises json.JSONDecodeError."""
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json {", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        LoadConfig(str(bad))()
