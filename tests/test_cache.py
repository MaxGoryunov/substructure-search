from app.cache import build_search_cache_key
from app.repositories import StoredMolecule


def test_search_cache_key_is_stable_for_same_dataset() -> None:
    molecules = [
        StoredMolecule(identifier="two", smiles="CCN"),
        StoredMolecule(identifier="one", smiles="CCO"),
    ]
    reordered = [
        StoredMolecule(identifier="one", smiles="CCO"),
        StoredMolecule(identifier="two", smiles="CCN"),
    ]

    assert build_search_cache_key("CC", molecules) == build_search_cache_key(
        "CC",
        reordered,
    )


def test_search_cache_key_changes_when_dataset_changes() -> None:
    original = [StoredMolecule(identifier="one", smiles="CCO")]
    changed = [StoredMolecule(identifier="one", smiles="CCN")]

    assert build_search_cache_key("CC", original) != build_search_cache_key(
        "CC",
        changed,
    )


def test_search_cache_key_changes_when_query_changes() -> None:
    molecules = [StoredMolecule(identifier="one", smiles="CCO")]

    assert build_search_cache_key("CC", molecules) != build_search_cache_key(
        "CO",
        molecules,
    )
