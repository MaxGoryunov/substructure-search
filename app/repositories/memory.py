"""In-memory molecule repository used before the database milestone."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredMolecule:
    """Molecule record stored by the application."""

    identifier: str
    smiles: str


class MoleculeNotFoundError(KeyError):
    """Raised when a molecule identifier is not present in storage."""


class DuplicateMoleculeError(ValueError):
    """Raised when a molecule identifier already exists."""


class InMemoryMoleculeRepository:
    """Small repository backed by a dictionary."""

    def __init__(self) -> None:
        self._molecules: dict[str, StoredMolecule] = {}

    def add(self, molecule: StoredMolecule) -> StoredMolecule:
        if molecule.identifier in self._molecules:
            raise DuplicateMoleculeError(molecule.identifier)
        self._molecules[molecule.identifier] = molecule
        return molecule

    def get(self, identifier: str) -> StoredMolecule:
        try:
            return self._molecules[identifier]
        except KeyError as exc:
            raise MoleculeNotFoundError(identifier) from exc

    def update(self, identifier: str, *, smiles: str) -> StoredMolecule:
        if identifier not in self._molecules:
            raise MoleculeNotFoundError(identifier)
        molecule = StoredMolecule(identifier=identifier, smiles=smiles)
        self._molecules[identifier] = molecule
        return molecule

    def delete(self, identifier: str) -> None:
        if identifier not in self._molecules:
            raise MoleculeNotFoundError(identifier)
        del self._molecules[identifier]

    def list(self, *, limit: int | None = None) -> Iterator[StoredMolecule]:
        count = 0
        for molecule in self._molecules.values():
            if limit is not None and count >= limit:
                return
            yield molecule
            count += 1

    def clear(self) -> None:
        self._molecules.clear()
