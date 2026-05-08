import pytest

from app.core import InvalidSmilesError, substructure_search


def test_finds_benzene_substructure() -> None:
    molecules = ["CCO", "c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O"]

    result = substructure_search(molecules, "c1ccccc1")

    assert result == ["c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O"]


def test_finds_carboxylic_acid_substructure() -> None:
    molecules = ["CCO", "CC(=O)O", "Cc1ccccc1"]

    result = substructure_search(molecules, "C(=O)O")

    assert result == ["CC(=O)O"]


def test_returns_empty_list_when_no_molecules_match() -> None:
    molecules = ["CCO", "CCN"]

    result = substructure_search(molecules, "c1ccccc1")

    assert result == []


def test_returns_empty_list_for_empty_input() -> None:
    assert substructure_search([], "c1ccccc1") == []


def test_skips_invalid_molecules_in_batch() -> None:
    molecules = ["not-smiles", "c1ccccc1"]

    result = substructure_search(molecules, "c1ccccc1")

    assert result == ["c1ccccc1"]


def test_raises_for_invalid_substructure() -> None:
    with pytest.raises(InvalidSmilesError):
        substructure_search(["c1ccccc1"], "not-smiles")
