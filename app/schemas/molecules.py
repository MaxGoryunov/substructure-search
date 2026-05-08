"""Pydantic schemas for molecule APIs."""

from pydantic import BaseModel, Field


class MoleculeCreate(BaseModel):
    identifier: str = Field(..., min_length=1)
    smiles: str = Field(..., min_length=1)


class MoleculeUpdate(BaseModel):
    smiles: str = Field(..., min_length=1)


class MoleculeRead(BaseModel):
    identifier: str
    smiles: str


class SearchRequest(BaseModel):
    substructure: str = Field(..., min_length=1)


class SearchResponse(BaseModel):
    substructure: str
    matches: list[MoleculeRead]
