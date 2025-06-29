from __future__ import annotations

import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
    level=logging.INFO,
)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the specified *name*."""
    return logging.getLogger(name)
