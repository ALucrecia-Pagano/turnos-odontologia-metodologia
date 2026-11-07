"""Servicio de lectura de la agenda (C-24).

Solo consulta: no hace commit ni rollback y no usa el reloj. La ventana se
interpreta en la zona horaria recibida (APP_TIMEZONE).
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.domain.model import Block, WorkingHours
from app.repositories.appointment import (
    AppointmentRepository,
    AppointmentWithNames,
    SqlAppointmentReader,
)
from app.repositories.blocks import BlockRepository
from app.repositories.working_hours import WorkingHoursRepository


@dataclass(frozen=True, slots=True)
class AgendaAppointment:
    id: UUID
    patient_id: UUID
    patient_name: str
    professional_id: UUID
    professional_name: str
    chair_id: UUID
    chair_name: str
    service_id: UUID
    service_name: str
    start_at: datetime
    end_at: datetime
    status: str


@dataclass(frozen=True, slots=True)
class Agenda:
    from_date: date
    to_date: date
    timezone: str
    appointments: tuple[AgendaAppointment, ...]
    working_hours: tuple[WorkingHours, ...]
    blocks: tuple[Block, ...]


def _to_agenda_appointment(row: AppointmentWithNames) -> AgendaAppointment:
    appointment = row.appointment
    return AgendaAppointment(
        id=appointment.id,
        patient_id=appointment.patient_id,
        patient_name=row.patient_name,
        professional_id=appointment.professional_id,
        professional_name=row.professional_name,
        chair_id=appointment.chair_id,
        chair_name=row.chair_name,
        service_id=appointment.service_id,
        service_name=row.service_name,
        start_at=appointment.start_at,
        end_at=appointment.end_at,
        status=appointment.status.value,
    )


def get_agenda(
    session: Session,
    from_date: date,
    to_date: date,
    professional_id: UUID | None,
    chair_id: UUID | None,
    tz: ZoneInfo,
) -> Agenda:
    window_start = datetime.combine(from_date, time.min, tzinfo=tz)
    window_end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=tz)

    rows = AppointmentRepository(session).list_for_agenda_in_range(
        window_start, window_end, professional_id=professional_id, chair_id=chair_id
    )
    blocks = BlockRepository(session, SqlAppointmentReader(session)).list_in_range(
        window_start, window_end, professional_id=professional_id
    )
    hours_repo = WorkingHoursRepository(session)
    working_hours = (
        hours_repo.list()
        if professional_id is None
        else hours_repo.list_by_professional(professional_id)
    )
    return Agenda(
        from_date=from_date,
        to_date=to_date,
        timezone=tz.key,
        appointments=tuple(_to_agenda_appointment(row) for row in rows),
        working_hours=working_hours,
        blocks=blocks,
    )


def get_agenda_appointment(session: Session, identifier: UUID) -> AgendaAppointment | None:
    row = AppointmentRepository(session).get_with_names(identifier)
    return None if row is None else _to_agenda_appointment(row)
