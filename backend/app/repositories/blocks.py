from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import BlockModel
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import Appointment, Block
from app.domain.rules.blocks import appointments_affected_by_block, validate_block
from app.domain.rules.references import unknown_reference_violation
from app.domain.violations import ReferenceKind, Rejected
from app.repositories._integrity import constraint_name
from app.repositories.contracts import AppointmentReader


def _unknown_reference(professional_id: UUID) -> Rejected:
    return Rejected(
        (
            unknown_reference_violation(ReferenceKind.PROFESSIONAL, professional_id),
        )
    )


class BlockRepository:
    def __init__(self, session: Session, appointment_reader: AppointmentReader) -> None:
        self._session = session
        self._appointment_reader = appointment_reader

    def create(self, candidate: Block) -> CatalogResult[Block]:
        violations = validate_block(candidate)
        if violations:
            return Rejected(tuple(violations))
        try:
            with self._session.begin_nested():
                self._session.add(
                    BlockModel(
                        id=candidate.id,
                        professional_id=candidate.professional_id,
                        start_at=candidate.start_at,
                        end_at=candidate.end_at,
                        reason=candidate.reason,
                    )
                )
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "fk_block_professional_id_professional":
                return _unknown_reference(candidate.professional_id)
            raise
        return Ok(candidate)

    def delete(self, identifier: UUID) -> Block | None:
        row = self._session.get(BlockModel, identifier)
        if row is None:
            return None
        entity = self._to_domain(row)
        self._session.delete(row)
        self._session.flush()
        return entity

    def get_by_id(self, identifier: UUID) -> Block | None:
        row = self._session.get(BlockModel, identifier)
        return None if row is None else self._to_domain(row)

    def list_by_professional(self, professional_id: UUID) -> tuple[Block, ...]:
        rows = self._session.scalars(
            select(BlockModel)
            .where(BlockModel.professional_id == professional_id)
            .order_by(BlockModel.start_at, BlockModel.id)
        ).all()
        return tuple(self._to_domain(row) for row in rows)

    def list_by_professional_in_range(
        self,
        professional_id: UUID,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> tuple[Block, ...]:
        stmt = select(BlockModel).where(BlockModel.professional_id == professional_id)
        if start_at is not None:
            stmt = stmt.where(BlockModel.end_at > start_at)
        if end_at is not None:
            stmt = stmt.where(BlockModel.start_at < end_at)
        stmt = stmt.order_by(BlockModel.start_at, BlockModel.id)
        rows = self._session.scalars(stmt).all()
        return tuple(self._to_domain(row) for row in rows)

    def list_in_range(
        self,
        start_at: datetime,
        end_at: datetime,
        professional_id: UUID | None = None,
    ) -> tuple[Block, ...]:
        stmt = select(BlockModel).where(
            BlockModel.start_at < end_at,
            BlockModel.end_at > start_at,
        )
        if professional_id is not None:
            stmt = stmt.where(BlockModel.professional_id == professional_id)
        stmt = stmt.order_by(BlockModel.start_at, BlockModel.id)
        return tuple(self._to_domain(row) for row in self._session.scalars(stmt).all())

    def list(self) -> tuple[Block, ...]:
        rows = self._session.scalars(
            select(BlockModel).order_by(BlockModel.start_at, BlockModel.id)
        ).all()
        return tuple(self._to_domain(row) for row in rows)

    def list_affected_appointments(self, block: Block) -> tuple[Appointment, ...]:
        candidates: Sequence[Appointment] = (
            self._appointment_reader.list_for_professional_in_range(
                block.professional_id,
                block.start_at,
                block.end_at,
            )
            if block.start_at < block.end_at
            else ()
        )
        return tuple(appointments_affected_by_block(block, candidates))

    @staticmethod
    def _to_domain(row: BlockModel) -> Block:
        return Block(
            row.id,
            row.professional_id,
            row.start_at,
            row.end_at,
            row.reason,
        )
