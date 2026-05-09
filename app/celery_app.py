"""Celery application configuration."""

from __future__ import annotations

from os import getenv

from celery import Celery


def _redis_url() -> str:
    return getenv("REDIS_URL", "redis://redis:6379/0")


celery_app = Celery(
    "substructure_search",
    broker=getenv("CELERY_BROKER_URL", _redis_url()),
    backend=getenv("CELERY_RESULT_BACKEND", _redis_url()),
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
