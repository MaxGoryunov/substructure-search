"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, status
from rdkit import Chem
from starlette.responses import Response

from app.core import InvalidSmilesError, substructure_search
from app.repositories import (
    DuplicateMoleculeError,
    InMemoryMoleculeRepository,
    MoleculeNotFoundError,
    StoredMolecule,
)
from app.schemas import (
    MoleculeCreate,
    MoleculeRead,
    MoleculeUpdate,
    SearchRequest,
    SearchResponse,
)

repository = InMemoryMoleculeRepository()
app = FastAPI(title="Substructure Search")


def _to_schema(molecule: StoredMolecule) -> MoleculeRead:
    return MoleculeRead(identifier=molecule.identifier, smiles=molecule.smiles)


def _ensure_valid_molecule_smiles(smiles: str) -> None:
    if Chem.MolFromSmiles(smiles) is None:
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


@app.post(
    "/molecules",
    response_model=MoleculeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_molecule(payload: MoleculeCreate) -> MoleculeRead:
    _ensure_valid_molecule_smiles(payload.smiles)
    molecule = StoredMolecule(identifier=payload.identifier, smiles=payload.smiles)
    try:
        return _to_schema(repository.add(molecule))
    except DuplicateMoleculeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Molecule {payload.identifier!r} already exists",
        ) from exc


@app.get("/molecules/{identifier}", response_model=MoleculeRead)
def get_molecule(identifier: str) -> MoleculeRead:
    try:
        return _to_schema(repository.get(identifier))
    except MoleculeNotFoundError as exc:
        raise _not_found(identifier) from exc


@app.put("/molecules/{identifier}", response_model=MoleculeRead)
def update_molecule(identifier: str, payload: MoleculeUpdate) -> MoleculeRead:
    _ensure_valid_molecule_smiles(payload.smiles)
    try:
        return _to_schema(repository.update(identifier, smiles=payload.smiles))
    except MoleculeNotFoundError as exc:
        raise _not_found(identifier) from exc


@app.delete("/molecules/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_molecule(identifier: str) -> Response:
    try:
        repository.delete(identifier)
    except MoleculeNotFoundError as exc:
        raise _not_found(identifier) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/molecules", response_model=list[MoleculeRead])
def list_molecules(limit: int | None = Query(default=None, ge=0)) -> list[MoleculeRead]:
    return [_to_schema(molecule) for molecule in repository.list(limit=limit)]


@app.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    molecules = list(repository.list())
    try:
        matched_smiles = substructure_search(
            (molecule.smiles for molecule in molecules),
            payload.substructure,
        )
    except InvalidSmilesError as exc:
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

    return SearchResponse(substructure=payload.substructure, matches=matches)
