"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from os import getenv

from fastapi import FastAPI, HTTPException, Query, status
from rdkit import Chem
from starlette.responses import Response

from app.cache import build_search_cache, build_search_cache_key
from app.config import get_database_url
from app.core import InvalidSmilesError, substructure_search
from app.db import build_session_factory
from app.logging_config import configure_logging
from app.repositories import (
    DuplicateMoleculeError,
    InMemoryMoleculeRepository,
    MoleculeNotFoundError,
    SQLAlchemyMoleculeRepository,
    StoredMolecule,
)
from app.schemas import (
    MoleculeCreate,
    MoleculeRead,
    MoleculeUpdate,
    SearchRequest,
    SearchResponse,
)

configure_logging()
logger = logging.getLogger(__name__)


def _build_repository() -> InMemoryMoleculeRepository | SQLAlchemyMoleculeRepository:
    database_url = get_database_url()
    if database_url is None:
        logger.info("using in-memory molecule repository")
        return InMemoryMoleculeRepository()
    logger.info("using SQLAlchemy molecule repository")
    return SQLAlchemyMoleculeRepository(build_session_factory(database_url))


repository = _build_repository()
search_cache = build_search_cache()
app = FastAPI(title="Substructure Search")


def _to_schema(molecule: StoredMolecule) -> MoleculeRead:
    return MoleculeRead(identifier=molecule.identifier, smiles=molecule.smiles)


def _to_cache_payload(matches: list[MoleculeRead]) -> list[dict[str, str]]:
    return [
        {"identifier": molecule.identifier, "smiles": molecule.smiles}
        for molecule in matches
    ]


def _from_cache_payload(matches: list[dict[str, str]]) -> list[MoleculeRead]:
    return [MoleculeRead(**molecule) for molecule in matches]


def _ensure_valid_molecule_smiles(smiles: str) -> None:
    if Chem.MolFromSmiles(smiles) is None:
        logger.warning("validation error for molecule SMILES")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid molecule SMILES: {smiles!r}",
        )


def _not_found(identifier: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Molecule {identifier!r} was not found",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/server")
def server() -> dict[str, str]:
    return {"server_id": getenv("SERVER_ID", "local")}


@app.post(
    "/molecules",
    response_model=MoleculeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_molecule(payload: MoleculeCreate) -> MoleculeRead:
    _ensure_valid_molecule_smiles(payload.smiles)
    molecule = StoredMolecule(identifier=payload.identifier, smiles=payload.smiles)
    try:
        created = repository.add(molecule)
        logger.info("created molecule", extra={"identifier": payload.identifier})
        return _to_schema(created)
    except DuplicateMoleculeError as exc:
        logger.warning(
            "duplicate molecule identifier",
            extra={"identifier": payload.identifier},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Molecule {payload.identifier!r} already exists",
        ) from exc


@app.get("/molecules/{identifier}", response_model=MoleculeRead)
def get_molecule(identifier: str) -> MoleculeRead:
    try:
        molecule = repository.get(identifier)
        logger.info("read molecule", extra={"identifier": identifier})
        return _to_schema(molecule)
    except MoleculeNotFoundError as exc:
        logger.warning("molecule not found", extra={"identifier": identifier})
        raise _not_found(identifier) from exc


@app.put("/molecules/{identifier}", response_model=MoleculeRead)
def update_molecule(identifier: str, payload: MoleculeUpdate) -> MoleculeRead:
    _ensure_valid_molecule_smiles(payload.smiles)
    try:
        updated = repository.update(identifier, smiles=payload.smiles)
        logger.info("updated molecule", extra={"identifier": identifier})
        return _to_schema(updated)
    except MoleculeNotFoundError as exc:
        logger.warning("molecule not found for update", extra={"identifier": identifier})
        raise _not_found(identifier) from exc


@app.delete("/molecules/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_molecule(identifier: str) -> Response:
    try:
        repository.delete(identifier)
    except MoleculeNotFoundError as exc:
        logger.warning("molecule not found for delete", extra={"identifier": identifier})
        raise _not_found(identifier) from exc
    logger.info("deleted molecule", extra={"identifier": identifier})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/molecules", response_model=list[MoleculeRead])
def list_molecules(limit: int | None = Query(default=None, ge=0)) -> list[MoleculeRead]:
    molecules = [_to_schema(molecule) for molecule in repository.list(limit=limit)]
    logger.info(
        "listed molecules",
        extra={"limit": limit, "result_count": len(molecules)},
    )
    return molecules


@app.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    molecules = list(repository.list())
    cache_key = build_search_cache_key(payload.substructure, molecules)
    if search_cache is not None:
        cached_matches = search_cache.get(cache_key)
        if cached_matches is not None:
            logger.info("search cache hit")
            return SearchResponse(
                substructure=payload.substructure,
                matches=_from_cache_payload(cached_matches),
            )
        logger.info("search cache miss")

    try:
        matched_smiles = substructure_search(
            (molecule.smiles for molecule in molecules),
            payload.substructure,
        )
    except InvalidSmilesError as exc:
        logger.warning("validation error for substructure SMILES")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    remaining = list(matched_smiles)
    matches: list[MoleculeRead] = []
    for molecule in molecules:
        if molecule.smiles in remaining:
            matches.append(_to_schema(molecule))
            remaining.remove(molecule.smiles)

    logger.info(
        "completed substructure search",
        extra={"molecule_count": len(molecules), "match_count": len(matches)},
    )
    if search_cache is not None:
        search_cache.set(cache_key, _to_cache_payload(matches))
    return SearchResponse(substructure=payload.substructure, matches=matches)
