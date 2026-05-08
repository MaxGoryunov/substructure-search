"""SQLAlchemy-backed molecule repository."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import String, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from app.db import Base
from app.repositories.memory import (
    DuplicateMoleculeError,
    MoleculeNotFoundError,
    StoredMolecule,
)


class MoleculeRecord(Base):
    """Persistent molecule table."""

    __tablename__ = "molecules"

    identifier: Mapped[str] = mapped_column(String(255), primary_key=True)
    smiles: Mapped[str] = mapped_column(String(2048), nullable=False)


class SQLAlchemyMoleculeRepository:
    """Repository backed by a SQLAlchemy session factory."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, molecule: StoredMolecule) -> StoredMolecule:
        with self._session_factory() as session:
            record = MoleculeRecord(
                identifier=molecule.identifier,
                smiles=molecule.smiles,
            )
            session.add(record)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateMoleculeError(molecule.identifier) from exc
            return molecule

    def get(self, identifier: str) -> StoredMolecule:
        with self._session_factory() as session:
            record = self._get_record(session, identifier)
            return self._to_stored(record)

    def update(self, identifier: str, *, smiles: str) -> StoredMolecule:
        with self._session_factory() as session:
            record = self._get_record(session, identifier)
            record.smiles = smiles
            session.commit()
            return self._to_stored(record)

    def delete(self, identifier: str) -> None:
        with self._session_factory() as session:
            record = self._get_record(session, identifier)
            session.delete(record)
            session.commit()

    def list(self, *, limit: int | None = None) -> Iterator[StoredMolecule]:
        with self._session_factory() as session:
            statement = select(MoleculeRecord).order_by(MoleculeRecord.identifier)
            if limit is not None:
                statement = statement.limit(limit)
            for record in session.scalars(statement):
                yield self._to_stored(record)

    def clear(self) -> None:
        with self._session_factory() as session:
            session.execute(delete(MoleculeRecord))
            session.commit()

    def _get_record(self, session: Session, identifier: str) -> MoleculeRecord:
        record = session.get(MoleculeRecord, identifier)
        if record is None:
            raise MoleculeNotFoundError(identifier)
        return record

    def _to_stored(self, record: MoleculeRecord) -> StoredMolecule:
        return StoredMolecule(identifier=record.identifier, smiles=record.smiles)
