"""RDKit-powered substructure search."""

from __future__ import annotations

from collections.abc import Iterable

from rdkit import Chem


class InvalidSmilesError(ValueError):
    """Raised when a SMILES string cannot be parsed by RDKit."""


def _parse_smiles(smiles: str, *, field_name: str) -> Chem.Mol:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise InvalidSmilesError(f"Invalid {field_name} SMILES: {smiles!r}")
    return molecule


def substructure_search(molecules: Iterable[str], substructure: str) -> list[str]:
    """Return molecules that contain the requested substructure.

    Invalid molecule SMILES are skipped so a batch search can still complete.
    An invalid substructure raises ``InvalidSmilesError`` because the query
    itself cannot be evaluated.
    """

    query = _parse_smiles(substructure, field_name="substructure")
    matches: list[str] = []

    for smiles in molecules:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            continue
        if molecule.HasSubstructMatch(query):
            matches.append(smiles)

    return matches
