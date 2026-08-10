"""Central logging setup.

Replaces scattered `print()` calls with a real logger so GitHub Actions
output gets consistent, filterable, leveled lines (and this also makes it
trivial to add a file handler later if we ever want persistent local logs).

Usage:
    from lib.logging_config import get_logger
    log = get_logger(__name__)
    log.info("Fetching release: %s/%s", owner, repo)
"""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)
