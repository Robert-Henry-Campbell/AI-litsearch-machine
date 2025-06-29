from __future__ import annotations

import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
    level=logging.INFO,
)


def format_exception(exc: Exception) -> str:
    """Return a concise representation of *exc* for logging."""
    return f"{type(exc).__name__}: {str(exc).splitlines()[0]}"


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the specified *name*."""
    return logging.getLogger(name)
