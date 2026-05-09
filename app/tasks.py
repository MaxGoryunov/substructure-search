"""Celery tasks."""

from __future__ import annotations

import logging

from app.cache import build_search_cache
from app.celery_app import celery_app
from app.repository_factory import build_molecule_repository
from app.search_service import search_stored_molecules

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.run_substructure_search")
def run_substructure_search(substructure: str) -> dict:
    logger.info("started search task")
    repository = build_molecule_repository()
    response = search_stored_molecules(
        repository,
        substructure,
        search_cache=build_search_cache(),
    )
    logger.info("completed search task")
    return response.model_dump()
