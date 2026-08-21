"""Configuration data classes, JSON/YAML loader, and alpha validator.

Three frozen dataclasses form the runtime configuration object graph:

* ``Runtime`` — random seed, log level, output directory.
* ``Optimization`` — alpha, method, enforce-nu-greater-than-six flag.
* ``Experiment`` — top-level config that nests both via ``Runtime`` /
  ``Optimization`` fields.

Use ``load(path)`` to read a JSON or YAML file (or ``load(None)`` for
defaults), and ``validate(config)`` to enforce semantic bounds.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Runtime:
    """Runtime knobs for deterministic and auditable execution.

    Attributes:
        seed: Random seed passed to numpy.
        log_level: stdlib ``logging`` level name.
        output_directory: Directory for saved reports.
    """

    seed: int = 7
    log_level: str = "INFO"
    output_directory: str = "artifacts"


@dataclass(frozen=True)
class Optimization:
    """Optimization inputs.

    Attributes:
        alpha: Confidence level in ``(0, 0.5)``.
        method: Optimization method selector.
        enforce_nu_greater_than_six: Whether to enforce ``nu > 6``.
    """

    alpha: float = 0.05
    method: str = "all"
    enforce_nu_greater_than_six: bool = True


@dataclass(frozen=True)
class Experiment:
    """Top-level package configuration.

    Attributes:
        runtime: Runtime knobs (seed, log level, output directory).
        optimization: Optimization inputs (alpha, method, ...).
    """

    runtime: Runtime = field(default_factory=Runtime)
    optimization: Optimization = field(default_factory=Optimization)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file using PyYAML. Raises ``ImportError`` if missing."""
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load(path: str | None) -> Experiment:
    """Load an ``Experiment`` from a JSON or YAML file.

    Args:
        path: Path to a ``.json`` or ``.yaml`` / ``.yml`` file,
            or ``None`` for default values.

    Returns:
        The loaded ``Experiment``. ``validate`` is run on the result.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        yaml.YAMLError: If the file is not valid YAML (and PyYAML is installed).
        ValueError: If the alpha bound is invalid.
    """
    if path is None:
        return Experiment()
    input_path = Path(path)
    suffix = input_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        raw_config = _load_yaml(input_path)
    else:
        raw_config = json.loads(input_path.read_text(encoding="utf-8"))
    raw_runtime = raw_config.get("runtime", {})
    raw_optimization = raw_config.get("optimization", {})
    if "output_dir" in raw_runtime and "output_directory" not in raw_runtime:
        raw_runtime["output_directory"] = raw_runtime.pop("output_dir")
    runtime = Runtime(**raw_runtime)
    optimization = Optimization(**raw_optimization)
    config = Experiment(runtime=runtime, optimization=optimization)
    validate(config)
    return config


def validate(config: Experiment) -> None:
    """Validate semantic constraints for safe operation.

    Args:
        config: The configuration to validate.

    Raises:
        ValueError: If ``config.optimization.alpha`` falls outside ``(0, 0.5)``.
    """
    if not (0.0 < config.optimization.alpha < 0.5):
        raise ValueError("alpha must satisfy 0 < alpha < 0.5")
