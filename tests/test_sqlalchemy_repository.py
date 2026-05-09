from app.db import build_session_factory
from app.repositories import (
    DuplicateMoleculeError,
    MoleculeNotFoundError,
    SQLAlchemyMoleculeRepository,
    StoredMolecule,
)


def test_sqlalchemy_repository_persists_molecules(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'molecules.db'}"
    session_factory = build_session_factory(database_url)
    repository = SQLAlchemyMoleculeRepository(session_factory)

    repository.add(StoredMolecule(identifier="benzene", smiles="c1ccccc1"))
    reloaded = SQLAlchemyMoleculeRepository(build_session_factory(database_url))

    assert reloaded.get("benzene") == StoredMolecule(
        identifier="benzene",
        smiles="c1ccccc1",
    )


def test_sqlalchemy_repository_rejects_duplicate_identifiers(tmp_path) -> None:
    repository = SQLAlchemyMoleculeRepository(
        build_session_factory(f"sqlite+pysqlite:///{tmp_path / 'molecules.db'}"),
    )

    repository.add(StoredMolecule(identifier="ethanol", smiles="CCO"))

    try:
        repository.add(StoredMolecule(identifier="ethanol", smiles="CCO"))
    except DuplicateMoleculeError:
        return

    raise AssertionError("duplicate identifier was accepted")


def test_sqlalchemy_repository_raises_for_missing_identifier(tmp_path) -> None:
    repository = SQLAlchemyMoleculeRepository(
        build_session_factory(f"sqlite+pysqlite:///{tmp_path / 'molecules.db'}"),
    )

    try:
        repository.get("missing")
    except MoleculeNotFoundError:
        return

    raise AssertionError("missing identifier was returned")
