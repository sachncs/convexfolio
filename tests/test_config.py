"""Tests for the Load and Validate composition classes."""

import json
from pathlib import Path

import pytest

from convexfolio.config import Experiment, Load, Validate


def test_load_config_defaults() -> None:
    """Load(None)() returns a default Experiment."""
    experiment = Load(None)()
    assert experiment.optimization.alpha == 0.05


def test_validate_rejects_invalid_alpha(tmp_path: Path) -> None:
    """Validate raises ValueError on out-of-bounds alpha."""
    experiment = Load(None)()
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
        Load(str(config_file))()


def test_validate_alpha_zero_and_one_rejected(tmp_path: Path) -> None:
    """Alpha at the boundary (0 or 0.5) is rejected."""
    experiment = Load(None)()
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
        Load(str(config_file))()


def test_load_config_json_default_key_alias(tmp_path: Path) -> None:
    """Legacy 'output_dir' key is mapped to 'output_directory'."""
    raw_config = {
        "runtime": {"output_dir": "old_name_dir"},
        "optimization": {"alpha": 0.1},
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(raw_config), encoding="utf-8")
    experiment = Load(str(config_file))()
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
    experiment = Load(str(config_file))()
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
    experiment = Load(str(config_file))()
    assert experiment.runtime.seed == 5


def test_validate_accepts_default_experiment() -> None:
    """Validate(default Experiment) does not raise."""
    experiment = Load(None)()
    Validate(experiment)


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    """Missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        Load(str(tmp_path / "nonexistent.json"))()


def test_load_config_invalid_json_raises(tmp_path: Path) -> None:
    """Invalid JSON raises json.JSONDecodeError."""
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json {", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        Load(str(bad))()


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    """Unknown fields are reported instead of silently ignored."""
    config_file = tmp_path / "unknown.json"
    config_file.write_text('{"runtime": {"mystery": true}}', encoding="utf-8")
    with pytest.raises(ValueError, match="unknown runtime keys"):
        Load(str(config_file))()


def test_load_config_rejects_non_mapping_root(tmp_path: Path) -> None:
    """A list or scalar cannot be interpreted as configuration."""
    config_file = tmp_path / "list.json"
    config_file.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="config root"):
        Load(str(config_file))()


def test_load_file_does_not_mutate_input_mapping(tmp_path: Path) -> None:
    """Legacy output_dir handling is performed on a copy."""
    config_file = tmp_path / "alias.json"
    config_file.write_text(
        '{"runtime": {"output_dir": "reports"}}', encoding="utf-8"
    )
    loader = Load(str(config_file))
    loader.load_file()
    assert config_file.read_text(encoding="utf-8") == (
        '{"runtime": {"output_dir": "reports"}}'
    )


@pytest.mark.parametrize(
    ("section", "value", "message"),
    [
        ("runtime", [], "runtime must be a mapping"),
        ("optimization", [], "optimization must be a mapping"),
        ("inputs", [], "inputs must be a mapping"),
    ],
)
def test_load_config_rejects_non_mapping_sections(
    tmp_path: Path, section: str, value: list[object], message: str
) -> None:
    config_file = tmp_path / f"bad_{section}.json"
    config_file.write_text(json.dumps({section: value}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        Load(str(config_file))()


def test_load_config_rejects_unknown_optimization_and_input_keys(
    tmp_path: Path,
) -> None:
    for name, payload, message in [
        ("optimization", {"unexpected": 1}, "unknown optimization keys"),
        ("inputs", {"unexpected": 1}, "unknown inputs keys"),
    ]:
        config_file = tmp_path / f"unknown_{name}.json"
        config_file.write_text(json.dumps({name: payload}), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            Load(str(config_file))()


def test_experiment_shortcuts_require_inputs() -> None:
    experiment = Experiment()
    with pytest.raises(ValueError, match="no portfolio inputs"):
        _ = experiment.expected_payoff
    with pytest.raises(ValueError, match="no portfolio inputs"):
        _ = experiment.cost_vector
    with pytest.raises(ValueError, match="no portfolio inputs"):
        _ = experiment.precision_matrix
