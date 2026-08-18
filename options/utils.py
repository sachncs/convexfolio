"""Cross-cutting helpers for the options package."""

import json
import logging
from pathlib import Path

from options.config import Experiment


class Logger:
    """Logging facade over the stdlib ``logging`` module.

    Wraps a named stdlib logger with a fixed format. Single concrete class;
    no subclasses, no polymorphism.
    """

    def __init__(self, level: str, name: str = "options") -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                )
            )
            self.logger.addHandler(handler)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)


class Report:
    """Standard deterministic determinism result.

    Holds repeated pipeline runs and exposes ``.save(path)`` to persist the
    summary as JSON. Used by both ``determinism`` and ``pipeline``.
    """

    def __init__(
        self,
        config: Experiment,
        repetitions: int,
        results: list[dict[str, object]],
    ) -> None:
        if repetitions < 2:
            raise ValueError("repetitions must be >= 2")
        if len(results) != repetitions:
            raise ValueError("results length must equal repetitions")
        self.config = config
        self.repetitions = repetitions
        self.results = results
        serialized = [json.dumps(r, sort_keys=True) for r in results]
        self.serialized = serialized
        self.all_match = all(item == serialized[0] for item in serialized[1:])
        self.summary: dict[str, object] = {
            "deterministic": self.all_match,
            "repetitions": repetitions,
            "seed": config.runtime.seed,
            "reference": results[0],
        }

    @property
    def deterministic(self) -> bool:
        return bool(self.summary["deterministic"])

    @property
    def seed(self) -> int:
        return int(self.summary["seed"])

    @property
    def reference(self) -> dict[str, object]:
        return self.summary["reference"]

    def save(self, path: str) -> Path:
        """Persist the report summary as JSON. Returns the written path."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.summary, indent=2), encoding="utf-8"
        )
        return output_path
