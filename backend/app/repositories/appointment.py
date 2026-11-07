from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, Select, select
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
)
from app.domain.intervals import Interval
from app.domain.model import (
    Appointment,
    AppointmentStatus,
    AppointmentStatusChange,
    RescheduleDetail,
)


def _to_appointment_domain(row: AppointmentModel) -> Appointment:
    start_at = (
        row.start_at
        if row.start_at.tzinfo is not None
        else row.start_at.replace(tzinfo=timezone.utc)
    )
    end_at = (
        row.end_at
        if row.end_at.tzinfo is not None
        else row.end_at.replace(tzinfo=timezone.utc)
    )
    return Appointment(
        id=row.id,
        patient_id=row.patient_id,
        professional_id=row.professional_id,
        chair_id=row.chair_id,
        service_id=row.service_id,
        start_at=start_at,
        end_at=end_at,
        status=AppointmentStatus(row.status),
    )


def _to_status_change_domain(
    row: AppointmentStatusChangeModel,
) -> AppointmentStatusChange:
    changed_at = (
        row.changed_at
        if row.changed_at.tzinfo is not None
        else row.changed_at.replace(tzinfo=timezone.utc)
    )
    from_status = (
        AppointmentStatus(row.from_status) if row.from_status is not None else None
    )
    to_status = AppointmentStatus(row.to_status)

    reschedule: RescheduleDetail | None = None
    if row.reschedule_previous_start_at is not None:
        assert row.reschedule_previous_end_at is not None
        assert row.reschedule_new_start_at is not None
        assert row.reschedule_new_end_at is not None
        assert row.reschedule_previous_professional_id is not None
        assert row.reschedule_new_professional_id is not None
        assert row.reschedule_previous_chair_id is not None
        assert row.reschedule_new_chair_id is not None

        prev_start = (
            row.reschedule_previous_start_at
            if row.reschedule_previous_start_at.tzinfo is not None
            else row.reschedule_previous_start_at.replace(tzinfo=timezone.utc)
        )
        prev_end = (
            row.reschedule_previous_end_at
            if row.reschedule_previous_end_at.tzinfo is not None
            else row.reschedule_previous_end_at.replace(tzinfo=timezone.utc)
        )
        new_start = (
            row.reschedule_new_start_at
            if row.reschedule_new_start_at.tzinfo is not None
            else row.reschedule_new_start_at.replace(tzinfo=timezone.utc)
        )
        new_end = (
            row.reschedule_new_end_at
            if row.reschedule_new_end_at.tzinfo is not None
            else row.reschedule_new_end_at.replace(tzinfo=timezone.utc)
        )
        reschedule = RescheduleDetail(
            previous_interval=Interval(prev_start, prev_end),
            new_interval=Interval(new_start, new_end),
            previous_professional_id=row.reschedule_previous_professional_id,
            new_professional_id=row.reschedule_new_professional_id,
            previous_chair_id=row.reschedule_previous_chair_id,
            new_chair_id=row.reschedule_new_chair_id,
        )

    return AppointmentStatusChange(
        appointment_id=row.appointment_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=row.changed_by,
        changed_at=changed_at,
        reschedule=reschedule,
    )


@dataclass(frozen=True, slots=True)
class AppointmentWithNames:
    appointment: Appointment
    patient_name: str
    professional_name: str
    chair_name: str
    service_name: str


def _agenda_select() -> Select[AppointmentModel, str, str, str, str]:
    return (
        select(
            AppointmentModel,
            PatientModel.full_name,
            ProfessionalModel.full_name,
            ChairModel.name,
            ServiceModel.name,
        )
        .join(PatientModel, PatientModel.id == AppointmentModel.patient_id)
        .join(ProfessionalModel, ProfessionalModel.id == AppointmentModel.professional_id)
        .join(ChairModel, ChairModel.id == AppointmentModel.chair_id)
        .join(ServiceModel, ServiceModel.id == AppointmentModel.service_id)
    )


def _to_with_names(
    row: Row[AppointmentModel, str, str, str, str],
) -> AppointmentWithNames:
    model, patient_name, professional_name, chair_name, service_name = row
    return AppointmentWithNames(
        appointment=_to_appointment_domain(model),
        patient_name=patient_name,
        professional_name=professional_name,
        chair_name=chair_name,
        service_name=service_name,
    )


class SqlAppointmentReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_professional_in_range(
        self,
        professional_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> Sequence[Appointment]:
        rows = self._session.scalars(
            select(AppointmentModel)
            .where(
                AppointmentModel.professional_id == professional_id,
                AppointmentModel.start_at < end_at,
                AppointmentModel.end_at > start_at,
            )
            .order_by(AppointmentModel.start_at, AppointmentModel.id)
        ).all()
        return tuple(_to_appointment_domain(row) for row in rows)


class AppointmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._reader = SqlAppointmentReader(session)

    def get_by_id(self, identifier: UUID) -> Appointment | None:
        row = self._session.get(AppointmentModel, identifier)
        return None if row is None else _to_appointment_domain(row)

    def list_for_professional_in_range(
        self,
        professional_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> Sequence[Appointment]:
        return self._reader.list_for_professional_in_range(
            professional_id, start_at, end_at
        )

    def list_for_agenda_in_range(
        self,
        start_at: datetime,
        end_at: datetime,
        professional_id: UUID | None = None,
        chair_id: UUID | None = None,
    ) -> tuple[AppointmentWithNames, ...]:
        stmt = _agenda_select().where(
            AppointmentModel.start_at < end_at,
            AppointmentModel.end_at > start_at,
        )
        if professional_id is not None:
            stmt = stmt.where(AppointmentModel.professional_id == professional_id)
        if chair_id is not None:
            stmt = stmt.where(AppointmentModel.chair_id == chair_id)
        stmt = stmt.order_by(AppointmentModel.start_at, AppointmentModel.id)
        return tuple(_to_with_names(row) for row in self._session.execute(stmt).all())

    def get_with_names(self, identifier: UUID) -> AppointmentWithNames | None:
        row = self._session.execute(
            _agenda_select().where(AppointmentModel.id == identifier)
        ).first()
        return None if row is None else _to_with_names(row)

    def list_for_chair_in_range(
        self,
        chair_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> Sequence[Appointment]:
        rows = self._session.scalars(
            select(AppointmentModel)
            .where(
                AppointmentModel.chair_id == chair_id,
                AppointmentModel.start_at < end_at,
                AppointmentModel.end_at > start_at,
            )
            .order_by(AppointmentModel.start_at, AppointmentModel.id)
        ).all()
        return tuple(_to_appointment_domain(row) for row in rows)


class AppointmentStatusChangeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_appointment_id(
        self, appointment_id: UUID
    ) -> Sequence[AppointmentStatusChange]:
        rows = self._session.scalars(
            select(AppointmentStatusChangeModel)
            .where(AppointmentStatusChangeModel.appointment_id == appointment_id)
            .order_by(
                AppointmentStatusChangeModel.changed_at,
                AppointmentStatusChangeModel.id,
            )
        ).all()
        return tuple(_to_status_change_domain(row) for row in rows)
