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
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from convexfolio.arrays import Matrix, Vector
from convexfolio.errors import ValidationError
from convexfolio.types import FloatArray
from convexfolio.validation import validate_portfolio_dimensions


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
    output_directory: str = "site/artifacts"


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

    def __post_init__(self) -> None:
        """Copy and validate all portfolio arrays at construction time."""
        expected_payoff = Vector(self.expected_payoff).validate("expected_payoff")
        cost_vector = Vector(self.cost_vector).validate("cost_vector", positive=True)
        precision_matrix = Matrix(self.precision_matrix).validate("precision_matrix")
        validate_portfolio_dimensions(
            expected_payoff, cost_vector, precision_matrix
        )
        object.__setattr__(self, "expected_payoff", expected_payoff)
        object.__setattr__(self, "cost_vector", cost_vector)
        object.__setattr__(self, "precision_matrix", precision_matrix)

    @property
    def n_instruments(self) -> int:
        """Number of instruments in the portfolio.

        Returns:
            The length of ``cost_vector`` (and ``expected_payoff``).
        """
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
        """Shortcut to ``inputs.expected_payoff`` (raises if no inputs).

        Returns:
            The 1-D expected-payoff vector.

        Raises:
            ValueError: If ``self.inputs`` is ``None``.
        """
        if self.inputs is None:
            raise ValueError(
                "experiment has no portfolio inputs; "
                "provide 'inputs' in the config file"
            )
        return self.inputs.expected_payoff

    @property
    def cost_vector(self) -> FloatArray:
        """Shortcut to ``inputs.cost_vector`` (raises if no inputs).

        Returns:
            The 1-D cost vector.

        Raises:
            ValueError: If ``self.inputs`` is ``None``.
        """
        if self.inputs is None:
            raise ValueError(
                "experiment has no portfolio inputs; "
                "provide 'inputs' in the config file"
            )
        return self.inputs.cost_vector

    @property
    def precision_matrix(self) -> FloatArray:
        """Shortcut to ``inputs.precision_matrix`` (raises if no inputs).

        Returns:
            The 2-D precision matrix.

        Raises:
            ValueError: If ``self.inputs`` is ``None``.
        """
        if self.inputs is None:
            raise ValueError(
                "experiment has no portfolio inputs; "
                "provide 'inputs' in the config file"
            )
        return self.inputs.precision_matrix


class Load:
    """Load an :class:`Experiment` from a JSON or YAML file.

    Composition: stores the ``path`` in :meth:`__init__`; the file IO
    + validation happens in :meth:`__call__`. Result is a fully-built
    :class:`Experiment` (with ``Validate`` already run).

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
        """Store the path; actual file IO happens in :meth:`__call__`.

        Args:
            path: Path to a ``.json`` or ``.yaml`` / ``.yml`` file,
                or ``None`` to construct a default :class:`Experiment`.
        """
        self.path = path

    def __call__(self) -> Experiment:
        """Read the file (or build defaults), validate, return.

        Returns:
            The loaded :class:`Experiment`.
        """
        config = Experiment() if self.path is None else self.load_file()
        Validate(config)
        return config

    def load_file(self) -> Experiment:
        """Load, validate, and construct an experiment from ``self.path``."""
        path = self.path
        if path is None:
            raise ValidationError("Load.load_file called without a path")
        input_path = Path(path)
        suffix = input_path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            raw_config = yaml.safe_load(input_path.read_text(encoding="utf-8"))
        else:
            raw_config = json.loads(input_path.read_text(encoding="utf-8"))

        if not isinstance(raw_config, Mapping):
            raise ValidationError("config root must be a mapping")
        unknown_config_keys = set(raw_config) - {"runtime", "optimization", "inputs"}
        if unknown_config_keys:
            raise ValidationError(
                "unknown config keys: " + ", ".join(sorted(unknown_config_keys))
            )

        raw_runtime = raw_config.get("runtime", {})
        if not isinstance(raw_runtime, Mapping):
            raise ValidationError("runtime must be a mapping")
        runtime_values = dict(raw_runtime)
        if "output_dir" in runtime_values and "output_directory" not in runtime_values:
            runtime_values["output_directory"] = runtime_values.pop("output_dir")
        unknown_runtime_keys = set(runtime_values) - {
            "seed",
            "log_level",
            "output_directory",
        }
        if unknown_runtime_keys:
            raise ValidationError(
                "unknown runtime keys: " + ", ".join(sorted(unknown_runtime_keys))
            )

        raw_optimization = raw_config.get("optimization", {})
        if not isinstance(raw_optimization, Mapping):
            raise ValidationError("optimization must be a mapping")
        optimization_values = dict(raw_optimization)
        unknown_optimization_keys = set(optimization_values) - {
            "alpha",
            "method",
            "enforce_nu_greater_than_six",
        }
        if unknown_optimization_keys:
            raise ValidationError(
                "unknown optimization keys: "
                + ", ".join(sorted(unknown_optimization_keys))
            )

        runtime = Runtime(**runtime_values)
        optimization = Optimization(**optimization_values)
        raw_inputs = raw_config.get("inputs")
        portfolio_inputs: PortfolioInputs | None = None
        if raw_inputs is not None:
            if not isinstance(raw_inputs, Mapping):
                raise ValidationError("inputs must be a mapping")
            unknown_input_keys = set(raw_inputs) - {
                "expected_payoff",
                "cost_vector",
                "precision_matrix",
            }
            if unknown_input_keys:
                raise ValidationError(
                    "unknown inputs keys: " + ", ".join(sorted(unknown_input_keys))
                )
            portfolio_inputs = PortfolioInputs(
                expected_payoff=np.asarray(raw_inputs["expected_payoff"], dtype=float),
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

    The constructor raises ``ValueError`` if any constraint is
    violated. Currently enforces ``0 < config.optimization.alpha < 0.5``.

    Args:
        config: The configuration to validate.

    Attributes:
        config: See Args.

    Raises:
        ValueError: If ``config.optimization.alpha`` falls outside
            ``(0, 0.5)``.
    """

    def __init__(self, config: Experiment) -> None:
        """Run the validation; raise on failure, otherwise store config.

        Args:
            config: The configuration to validate.

        Raises:
            ValueError: If ``config.optimization.alpha`` falls outside
                ``(0, 0.5)``.
        """
        if not np.isfinite(config.optimization.alpha):
            raise ValidationError("alpha must be finite")
        if not (0.0 < config.optimization.alpha < 0.5):
            raise ValidationError("alpha must satisfy 0 < alpha < 0.5")
        self.config = config
