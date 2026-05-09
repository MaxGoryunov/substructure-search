"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from os import getenv

from fastapi import FastAPI, HTTPException, Query, status
from rdkit import Chem
from celery.result import AsyncResult
from starlette.responses import Response

from app.cache import build_search_cache
from app.celery_app import celery_app
from app.logging_config import configure_logging
from app.repository_factory import build_molecule_repository
from app.repositories import (
    DuplicateMoleculeError,
    MoleculeNotFoundError,
    StoredMolecule,
)
from app.schemas import (
    MoleculeCreate,
    MoleculeRead,
    MoleculeUpdate,
    SearchRequest,
    SearchResponse,
    SearchTaskStatus,
)
from app.search_service import InvalidSmilesError, search_stored_molecules
from app.tasks import run_substructure_search

configure_logging()
logger = logging.getLogger(__name__)

repository = build_molecule_repository()
search_cache = build_search_cache()
app = FastAPI(title="Substructure Search")


def _to_schema(molecule: StoredMolecule) -> MoleculeRead:
    return MoleculeRead(identifier=molecule.identifier, smiles=molecule.smiles)


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
        logger.warning(
            "molecule not found for update",
            extra={"identifier": identifier},
        )
        raise _not_found(identifier) from exc


@app.delete("/molecules/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_molecule(identifier: str) -> Response:
    try:
        repository.delete(identifier)
    except MoleculeNotFoundError as exc:
        logger.warning(
            "molecule not found for delete",
            extra={"identifier": identifier},
        )
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
    try:
        return search_stored_molecules(
            repository,
            payload.substructure,
            search_cache=search_cache,
        )
    except InvalidSmilesError as exc:
        logger.warning("validation error for substructure SMILES")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@app.post(
    "/search/tasks",
    response_model=SearchTaskStatus,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_search_task(payload: SearchRequest) -> SearchTaskStatus:
    task = run_substructure_search.delay(payload.substructure)
    logger.info("queued search task", extra={"task_id": task.id})
    return SearchTaskStatus(task_id=task.id, status=task.status)


@app.get("/search/tasks/{task_id}", response_model=SearchTaskStatus)
def get_search_task(task_id: str) -> SearchTaskStatus:
    task = AsyncResult(task_id, app=celery_app)
    logger.info("read search task status", extra={"task_id": task_id})
    if task.successful():
        return SearchTaskStatus(
            task_id=task_id,
            status=task.status,
            result=SearchResponse(**task.result),
        )
    if task.failed():
        return SearchTaskStatus(
            task_id=task_id,
            status=task.status,
            error=str(task.result),
        )
    return SearchTaskStatus(task_id=task_id, status=task.status)
