"""Cross-cutting helpers for the options package."""

import logging


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
