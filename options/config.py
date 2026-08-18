"""Configuration objects and validation for production pipelines."""

from dataclasses import dataclass
from dataclasses import field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime controls for deterministic and auditable execution."""

    seed: int = 7
    log_level: str = "INFO"
    output_dir: str = "artifacts"


@dataclass(frozen=True)
class OptimizationConfig:
    """Input controls for portfolio optimization routines."""

    alpha: float = 0.05
    method: str = "all"
    enforce_nu_greater_than_six: bool = True


@dataclass(frozen=True)
class ExperimentConfig:
    """Top-level package configuration."""

    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)


def load(path: str | None) -> ExperimentConfig:
    """Loads config from JSON. If absent, returns defaults.

    YAML is NOT DETERMINED for baseline dependencies minimization.
    """
    if path is None:
        return ExperimentConfig()
    input_path = Path(path)
    raw_config: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))
    runtime = RuntimeConfig(**raw_config.get("runtime", {}))
    optimization = OptimizationConfig(**raw_config.get("optimization", {}))
    config = ExperimentConfig(runtime=runtime, optimization=optimization)
    validate(config)
    return config


def validate(config: ExperimentConfig) -> None:
    """Validates semantic constraints for safe operation."""
    if not (0.0 < config.optimization.alpha < 0.5):
        raise ValueError("alpha must satisfy 0 < alpha < 0.5")
