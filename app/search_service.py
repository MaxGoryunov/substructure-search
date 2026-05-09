"""Application search workflow."""

from __future__ import annotations

import logging

from app.cache import RedisSearchCache, build_search_cache_key
from app.core import InvalidSmilesError, substructure_search
from app.repositories import InMemoryMoleculeRepository, SQLAlchemyMoleculeRepository
from app.schemas import MoleculeRead, SearchResponse

logger = logging.getLogger(__name__)

MoleculeRepository = InMemoryMoleculeRepository | SQLAlchemyMoleculeRepository


def _to_schema(identifier: str, smiles: str) -> MoleculeRead:
    return MoleculeRead(identifier=identifier, smiles=smiles)


def _to_cache_payload(matches: list[MoleculeRead]) -> list[dict[str, str]]:
    return [
        {"identifier": molecule.identifier, "smiles": molecule.smiles}
        for molecule in matches
    ]


def _from_cache_payload(matches: list[dict[str, str]]) -> list[MoleculeRead]:
    return [MoleculeRead(**molecule) for molecule in matches]


def search_stored_molecules(
    repository: MoleculeRepository,
    substructure: str,
    *,
    search_cache: RedisSearchCache | None = None,
) -> SearchResponse:
    molecules = list(repository.list())
    cache_key = build_search_cache_key(substructure, molecules)
    if search_cache is not None:
        cached_matches = search_cache.get(cache_key)
        if cached_matches is not None:
            logger.info("search cache hit")
            return SearchResponse(
                substructure=substructure,
                matches=_from_cache_payload(cached_matches),
            )
        logger.info("search cache miss")

    matched_smiles = substructure_search(
        (molecule.smiles for molecule in molecules),
        substructure,
    )

    remaining = list(matched_smiles)
    matches: list[MoleculeRead] = []
    for molecule in molecules:
        if molecule.smiles in remaining:
            matches.append(_to_schema(molecule.identifier, molecule.smiles))
            remaining.remove(molecule.smiles)

    logger.info(
        "completed substructure search",
        extra={"molecule_count": len(molecules), "match_count": len(matches)},
    )
    if search_cache is not None:
        search_cache.set(cache_key, _to_cache_payload(matches))
    return SearchResponse(substructure=substructure, matches=matches)


__all__ = ["InvalidSmilesError", "MoleculeRepository", "search_stored_molecules"]
