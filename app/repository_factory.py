"""Repository factory helpers."""

from __future__ import annotations

import logging

from app.config import get_database_url
from app.db import build_session_factory
from app.repositories import (
    InMemoryMoleculeRepository,
    SQLAlchemyMoleculeRepository,
)

logger = logging.getLogger(__name__)


def build_molecule_repository() -> (
    InMemoryMoleculeRepository | SQLAlchemyMoleculeRepository
):
    database_url = get_database_url()
    if database_url is None:
        logger.info("using in-memory molecule repository")
        return InMemoryMoleculeRepository()
    logger.info("using SQLAlchemy molecule repository")
    return SQLAlchemyMoleculeRepository(build_session_factory(database_url))
