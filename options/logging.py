"""Logging utilities for CLI and library usage."""

import logging


def configure_logging(level: str) -> None:
    """Configures package-level logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
