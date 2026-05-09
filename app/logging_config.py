"""Application logging setup."""

from __future__ import annotations

import logging
from os import getenv


def configure_logging() -> None:
    """Configure standard-library logging for the API process."""

    logging.basicConfig(
        level=getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
