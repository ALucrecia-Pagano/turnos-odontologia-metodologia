"""Servicios de aplicación para horarios de atención y bloqueos (C-21).

Transaccionalidad explícita con auto_commit=True.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.api.errors import DomainRejectedError, NotFoundError
from app.domain.model import Appointment, Block, WorkingHours
from app.domain.rules.working_hours import appointments_outside_working_hours
from app.domain.violations import Rejected
from app.repositories.appointment import AppointmentRepository, SqlAppointmentReader
from app.repositories.blocks import BlockRepository
from app.repositories.catalog import ProfessionalRepository
from app.repositories.patients import PatientRepository
from app.repositories.working_hours import WorkingHoursRepository
from app.services.appointments import _lock_resources


@dataclass(frozen=True, slots=True)
class AffectedAppointment:
    id: UUID
    patient_id: UUID
    patient_name: str
    chair_id: UUID
    start_at: datetime
    end_at: datetime
    status: str


def _affected_summary(
    session: Session, appointments: Sequence[Appointment]
) -> list[AffectedAppointment]:
    patient_repo = PatientRepository(session)
    patient_names: dict[UUID, str] = {}
    summary: list[AffectedAppointment] = []
    for apt in appointments:
        if apt.patient_id not in patient_names:
            pat = patient_repo.get_by_id(apt.patient_id)
            patient_names[apt.patient_id] = pat.full_name if pat else ""
        summary.append(
            AffectedAppointment(
                id=apt.id,
                patient_id=apt.patient_id,
                patient_name=patient_names[apt.patient_id],
                chair_id=apt.chair_id,
                start_at=apt.start_at,
                end_at=apt.end_at,
                status=apt.status.value,
            )
        )
    return summary


def get_working_hours(session: Session, professional_id: UUID) -> tuple[WorkingHours, ...]:
    prof = ProfessionalRepository(session).get_by_id(professional_id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")
    return WorkingHoursRepository(session).list_by_professional(professional_id)


def replace_working_hours(
    session: Session,
    professional_id: UUID,
    slots: Sequence[WorkingHours],
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> tuple[tuple[WorkingHours, ...], list[AffectedAppointment]]:
    prof = ProfessionalRepository(session).get_by_id(professional_id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")

    _lock_resources(session, professional_ids=[professional_id], chair_ids=[])

    repo = WorkingHoursRepository(session)
    res = repo.replace_for_professional(professional_id, slots)
    if isinstance(res, Rejected):
        raise DomainRejectedError(res)

    candidates = AppointmentRepository(session).list_for_professional_in_range(
        professional_id, now, now + timedelta(days=90)
    )
    outside = appointments_outside_working_hours(professional_id, candidates, slots, tz, now)
    affected = _affected_summary(session, outside)

    if auto_commit:
        session.commit()
    return res.entity, affected


def list_blocks(
    session: Session,
    professional_id: UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> tuple[Block, ...]:
    prof = ProfessionalRepository(session).get_by_id(professional_id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")
    repo = BlockRepository(session, SqlAppointmentReader(session))
    return repo.list_by_professional_in_range(
        professional_id, start_at=start_at, end_at=end_at
    )


def get_block(session: Session, block_id: UUID) -> Block:
    repo = BlockRepository(session, SqlAppointmentReader(session))
    block = repo.get_by_id(block_id)
    if block is None:
        raise NotFoundError("Bloqueo no encontrado.")
    return block


def create_block(
    session: Session,
    professional_id: UUID,
    start_at: datetime,
    end_at: datetime,
    reason: str | None = None,
    block_id: UUID | None = None,
    auto_commit: bool = True,
) -> tuple[Block, list[AffectedAppointment]]:
    prof = ProfessionalRepository(session).get_by_id(professional_id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")

    _lock_resources(session, professional_ids=[professional_id], chair_ids=[])

    candidate = Block(
        id=block_id or uuid4(),
        professional_id=professional_id,
        start_at=start_at,
        end_at=end_at,
        reason=reason,
    )
    repo = BlockRepository(session, SqlAppointmentReader(session))
    res = repo.create(candidate)
    if isinstance(res, Rejected):
        raise DomainRejectedError(res)

    affected_apts = repo.list_affected_appointments(res.entity)
    affected = _affected_summary(session, affected_apts)

    if auto_commit:
        session.commit()
    return res.entity, affected


def delete_block(session: Session, block_id: UUID, auto_commit: bool = True) -> Block:
    repo = BlockRepository(session, SqlAppointmentReader(session))
    deleted = repo.delete(block_id)
    if deleted is None:
        raise NotFoundError("Bloqueo no encontrado.")
    if auto_commit:
        session.commit()
    return deleted
