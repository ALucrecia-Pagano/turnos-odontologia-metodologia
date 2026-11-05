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
from app.domain.violations import ReferenceKind, Rejected, Violation, ViolationCode
from app.repositories.contracts import AppointmentReader


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


def _unknown_reference(professional_id: UUID) -> Rejected:
    return Rejected(
        (
            Violation(
                code=ViolationCode.UNKNOWN_REFERENCE,
                message=f"El profesional indicado no existe (id {professional_id}).",
                reference_kind=ReferenceKind.PROFESSIONAL,
            ),
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
            if _constraint_name(error) == "fk_block_professional_id_professional":
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
            _as_aware_datetime(row.start_at),
            _as_aware_datetime(row.end_at),
            row.reason,
        )


def _as_aware_datetime(value: datetime) -> datetime:
    return value
