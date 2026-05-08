"""Application configuration helpers."""

from __future__ import annotations

from os import getenv


def get_database_url() -> str | None:
    """Return the configured database URL, if persistent storage is enabled."""

    return getenv("DATABASE_URL")
