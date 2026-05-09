"""Search result caching helpers."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable
from os import getenv

from app.repositories import StoredMolecule

logger = logging.getLogger(__name__)


def build_dataset_fingerprint(molecules: Iterable[StoredMolecule]) -> str:
    digest = hashlib.sha256()
    for molecule in sorted(molecules, key=lambda item: item.identifier):
        digest.update(molecule.identifier.encode())
        digest.update(b"\0")
        digest.update(molecule.smiles.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def build_search_cache_key(
    substructure: str,
    molecules: Iterable[StoredMolecule],
) -> str:
    dataset_fingerprint = build_dataset_fingerprint(molecules)
    return f"search:{dataset_fingerprint}:{substructure}"


class RedisSearchCache:
    """Redis-backed cache for search responses."""

    def __init__(self, redis_url: str, *, ttl_seconds: int) -> None:
        from redis import Redis

        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> list[dict[str, str]] | None:
        try:
            payload = self._client.get(key)
        except Exception:
            logger.exception("redis cache read failed")
            return None
        if payload is None:
            return None
        return json.loads(payload)

    def set(self, key: str, matches: list[dict[str, str]]) -> None:
        try:
            self._client.setex(key, self._ttl_seconds, json.dumps(matches))
        except Exception:
            logger.exception("redis cache write failed")


def build_search_cache() -> RedisSearchCache | None:
    redis_url = getenv("REDIS_URL")
    if redis_url is None:
        logger.info("redis cache disabled")
        return None

    ttl_seconds = int(getenv("SEARCH_CACHE_TTL_SECONDS", "300"))
    logger.info("redis cache enabled", extra={"ttl_seconds": ttl_seconds})
    return RedisSearchCache(redis_url, ttl_seconds=ttl_seconds)
