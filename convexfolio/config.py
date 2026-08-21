"""Configuration data classes, loader class, and alpha validator class.

Four frozen dataclasses form the runtime configuration object graph:

* :class:`Runtime` — random seed, log level, output directory.
* :class:`Optimization` — alpha, method, enforce-nu-greater-than-six flag.
* :class:`PortfolioInputs` — expected payoff, cost vector, precision matrix.
* :class:`Experiment` — top-level config that nests the others.

Two composable classes drive the load + validate cycle:

* :class:`Load` — reads a JSON or YAML file and returns a
  fully-built :class:`Experiment`; validation is run on the result.
* :class:`Validate` — alpha-bounds checker; callable as
  ``Validate()(config)``.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from convexfolio.types import FloatArray


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
class PortfolioInputs:
    """Bundle of inputs required to solve an optimisation problem.

    Attributes:
        expected_payoff: 1-D expected-payoff vector ``u``.
        cost_vector: 1-D cost vector ``v``.
        precision_matrix: 2-D precision matrix ``Q``.
    """

    expected_payoff: FloatArray
    cost_vector: FloatArray
    precision_matrix: FloatArray

    @property
    def n_instruments(self) -> int:
        return int(self.cost_vector.shape[0])


@dataclass(frozen=True)
class Experiment:
    """Top-level package configuration.

    Attributes:
        runtime: Runtime knobs (seed, log level, output directory).
        optimization: Optimization inputs (alpha, method, ...).
        inputs: Portfolio inputs (expected_payoff, cost_vector,
            precision_matrix). Default is ``None``; populated when
            the config carries them.
    """

    runtime: Runtime = field(default_factory=Runtime)
    optimization: Optimization = field(default_factory=Optimization)
    inputs: PortfolioInputs | None = None

    @property
    def expected_payoff(self) -> FloatArray:
        assert self.inputs is not None, (
            "experiment has no portfolio inputs; "
            "provide 'inputs' in the config file"
        )
        return self.inputs.expected_payoff

    @property
    def cost_vector(self) -> FloatArray:
        assert self.inputs is not None, (
            "experiment has no portfolio inputs; "
            "provide 'inputs' in the config file"
        )
        return self.inputs.cost_vector

    @property
    def precision_matrix(self) -> FloatArray:
        assert self.inputs is not None, (
            "experiment has no portfolio inputs; "
            "provide 'inputs' in the config file"
        )
        return self.inputs.precision_matrix


class Load:
    """Load an :class:`Experiment` from a JSON or YAML file.

    Callable: ``Load(path)()`` returns the loaded
    :class:`Experiment`. ``Validate`` is run on the result.

    Args:
        path: Path to a ``.json`` or ``.yaml`` / ``.yml`` file,
            or ``None`` to construct a default :class:`Experiment`.

    Attributes:
        path: See Args.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        yaml.YAMLError: If the file is not valid YAML.
        ValueError: If the alpha bound is invalid.
    """

    def __init__(self, path: str | None) -> None:
        self.path = path

    def __call__(self) -> Experiment:
        config = Experiment() if self.path is None else self._from_file()
        Validate(config)
        return config

    def _from_file(self) -> Experiment:
        assert self.path is not None
        input_path = Path(self.path)
        suffix = input_path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            raw_config = yaml.safe_load(input_path.read_text(encoding="utf-8"))
        else:
            raw_config = json.loads(input_path.read_text(encoding="utf-8"))
        raw_runtime = raw_config.get("runtime", {})
        raw_optimization = raw_config.get("optimization", {})
        if "output_dir" in raw_runtime and "output_directory" not in raw_runtime:
            raw_runtime["output_directory"] = raw_runtime.pop("output_dir")
        runtime = Runtime(**raw_runtime)
        optimization = Optimization(**raw_optimization)
        raw_inputs = raw_config.get("inputs")
        portfolio_inputs: PortfolioInputs | None = None
        if raw_inputs is not None:
            portfolio_inputs = PortfolioInputs(
                expected_payoff=np.asarray(
                    raw_inputs["expected_payoff"], dtype=float
                ),
                cost_vector=np.asarray(raw_inputs["cost_vector"], dtype=float),
                precision_matrix=np.asarray(
                    raw_inputs["precision_matrix"], dtype=float
                ),
            )
        return Experiment(
            runtime=runtime,
            optimization=optimization,
            inputs=portfolio_inputs,
        )


class Validate:
    """Validate semantic constraints on an :class:`Experiment`.

    The constructor raises ``ValueError`` if any constraint is violated.
    Currently enforces ``0 < config.optimization.alpha < 0.5``.

    Args:
        config: The configuration to validate.

    Attributes:
        config: See Args.

    Raises:
        ValueError: If ``config.optimization.alpha`` falls outside
            ``(0, 0.5)``.
    """

    def __init__(self, config: Experiment) -> None:
        if not (0.0 < config.optimization.alpha < 0.5):
            raise ValueError("alpha must satisfy 0 < alpha < 0.5")
        self.config = config
