from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    HistoryEntryResponse,
    RescheduleDetailResponse,
    format_utc_iso,
)
from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    ProfessionalModel,
)
from app.domain.appointment.reschedule import reschedule_appointment as domain_reschedule_appointment
from app.domain.appointment.transitions import (
    cancel_appointment as domain_cancel_appointment,
    change_status as domain_change_status,
)
from app.domain.appointment.validate import validate_new_appointment
from app.domain.model import (
    Actor,
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    NewAppointmentRequest,
    RescheduleRequest,
    ScheduleContext,
)
from app.domain.violations import Ok, Rejected, ValidationResult
from app.repositories.appointment import (
    AppointmentRepository,
    AppointmentStatusChangeRepository,
    SqlAppointmentReader,
)
from app.repositories.blocks import BlockRepository
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from app.repositories.users import UserRepository
from app.repositories.working_hours import WorkingHoursRepository


def _lock_resources(
    session: Session,
    professional_ids: list[UUID],
    chair_ids: list[UUID],
) -> None:
    for prof_id in sorted(set(professional_ids)):
        session.execute(
            select(ProfessionalModel.id)
            .where(ProfessionalModel.id == prof_id)
            .with_for_update()
        )
    for chair_id in sorted(set(chair_ids)):
        session.execute(
            select(ChairModel.id)
            .where(ChairModel.id == chair_id)
            .with_for_update()
        )


def _load_references(session: Session, patient_id: UUID, professional_id: UUID, chair_id: UUID, service_id: UUID) -> AppointmentReferences:
    patient = PatientRepository(session).get_by_id(patient_id)
    professional = ProfessionalRepository(session).get_by_id(professional_id)
    chair = ChairRepository(session).get_by_id(chair_id)
    service = ServiceRepository(session).get_by_id(service_id)
    return AppointmentReferences(
        patient=patient,
        professional=professional,
        chair=chair,
        service=service,
    )


def _load_schedule_context(
    session: Session,
    professional_id: UUID,
    now: datetime,
    tz: ZoneInfo,
) -> ScheduleContext:
    working_hours = WorkingHoursRepository(session).list_by_professional(professional_id)
    reader = SqlAppointmentReader(session)
    blocks = BlockRepository(session, reader).list_by_professional(professional_id)
    return ScheduleContext(
        tz=tz,
        working_hours=working_hours,
        blocks=blocks,
        now=now,
    )


def book_appointment(
    session: Session,
    request: NewAppointmentRequest,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult:
    try:
        # 1. Bloqueo pesimista ordenado: professional ordenado -> chair ordenado
        _lock_resources(session, [request.professional_id], [request.chair_id])

        # 2. Cargar contexto dentro del bloqueo
        references = _load_references(
            session,
            request.patient_id,
            request.professional_id,
            request.chair_id,
            request.service_id,
        )
        context = _load_schedule_context(session, request.professional_id, now, tz)

        # Cargar turnos activos en rango del profesional y del sillón (margen 480 min)
        search_start = request.start_at - timedelta(minutes=480)
        search_end = request.start_at + timedelta(minutes=480)
        app_repo = AppointmentRepository(session)
        prof_apps = app_repo.list_for_professional_in_range(request.professional_id, search_start, search_end)
        chair_apps = app_repo.list_for_chair_in_range(request.chair_id, search_start, search_end)
        existing_dict = {a.id: a for a in (*prof_apps, *chair_apps)}
        existing_appointments = tuple(existing_dict.values())

        # 3. Invocar al dominio puro
        result = validate_new_appointment(
            request,
            references,
            existing_appointments,
            context,
        )

        if isinstance(result, Ok):
            appointment_entity: Appointment = result.appointment
            status_change = result.status_change

            app_model = AppointmentModel(
                id=appointment_entity.id,
                patient_id=appointment_entity.patient_id,
                professional_id=appointment_entity.professional_id,
                chair_id=appointment_entity.chair_id,
                service_id=appointment_entity.service_id,
                start_at=appointment_entity.start_at,
                end_at=appointment_entity.end_at,
                status=appointment_entity.status.value,
                created_at=status_change.changed_at,
                updated_at=status_change.changed_at,
            )
            session.add(app_model)

            change_model = AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=appointment_entity.id,
                from_status=None,
                to_status=status_change.to_status.value,
                changed_by=status_change.changed_by,
                changed_at=status_change.changed_at,
                note=None,
            )
            session.add(change_model)
            session.flush()

            if auto_commit:
                session.commit()
            return result
        else:
            session.rollback()
            return result
    except Exception:
        session.rollback()
        raise


def change_appointment_status(
    session: Session,
    appointment_id: UUID,
    target_status: AppointmentStatus,
    actor: Actor,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult | None:
    try:
        # D4 & D11: Bloqueo de fila del turno existente con SELECT ... FOR UPDATE
        row = session.scalars(
            select(AppointmentModel)
            .where(AppointmentModel.id == appointment_id)
            .with_for_update()
        ).first()
        if row is None:
            return None

        # Reconstruir estado actual del turno dentro del bloqueo
        appointment_entity = Appointment(
            id=row.id,
            patient_id=row.patient_id,
            professional_id=row.professional_id,
            chair_id=row.chair_id,
            service_id=row.service_id,
            start_at=row.start_at,
            end_at=row.end_at,
            status=AppointmentStatus(row.status),
        )

        professional = session.get(ProfessionalModel, appointment_entity.professional_id)
        professional_name = professional.full_name if professional is not None else ""

        result = domain_change_status(
            appointment_entity,
            target_status,
            actor,
            now,
            professional_name,
            tz,
        )

        if isinstance(result, Ok):
            row.status = result.appointment.status.value
            row.updated_at = result.status_change.changed_at

            from_status_val = (
                result.status_change.from_status.value
                if result.status_change.from_status is not None
                else None
            )
            change_model = AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=result.appointment.id,
                from_status=from_status_val,
                to_status=result.status_change.to_status.value,
                changed_by=result.status_change.changed_by,
                changed_at=result.status_change.changed_at,
                note=None,
            )
            session.add(change_model)
            session.flush()

            if auto_commit:
                session.commit()
            return result
        else:
            session.rollback()
            return result
    except Exception:
        session.rollback()
        raise


def cancel_appointment(
    session: Session,
    appointment_id: UUID,
    actor: Actor,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult | None:
    try:
        # D4 & D11: Bloqueo de fila del turno existente con SELECT ... FOR UPDATE
        row = session.scalars(
            select(AppointmentModel)
            .where(AppointmentModel.id == appointment_id)
            .with_for_update()
        ).first()
        if row is None:
            return None

        # Reconstruir estado actual del turno dentro del bloqueo
        appointment_entity = Appointment(
            id=row.id,
            patient_id=row.patient_id,
            professional_id=row.professional_id,
            chair_id=row.chair_id,
            service_id=row.service_id,
            start_at=row.start_at,
            end_at=row.end_at,
            status=AppointmentStatus(row.status),
        )

        professional = session.get(ProfessionalModel, appointment_entity.professional_id)
        professional_name = professional.full_name if professional is not None else ""

        result = domain_cancel_appointment(
            appointment_entity,
            actor,
            now,
            professional_name,
            tz,
        )

        if isinstance(result, Ok):
            row.status = result.appointment.status.value
            row.updated_at = result.status_change.changed_at

            from_status_val = (
                result.status_change.from_status.value
                if result.status_change.from_status is not None
                else None
            )
            change_model = AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=result.appointment.id,
                from_status=from_status_val,
                to_status=result.status_change.to_status.value,
                changed_by=result.status_change.changed_by,
                changed_at=result.status_change.changed_at,
                note=None,
            )
            session.add(change_model)
            session.flush()

            if auto_commit:
                session.commit()
            return result
        else:
            session.rollback()
            return result
    except Exception:
        session.rollback()
        raise


def reschedule_appointment(
    session: Session,
    appointment_id: UUID,
    request: RescheduleRequest,
    actor: Actor,
    now: datetime,
    tz: ZoneInfo,
    auto_commit: bool = True,
) -> ValidationResult | None:
    try:
        # D4 & D11: Bloqueo de fila del turno existente con SELECT ... FOR UPDATE
        row = session.scalars(
            select(AppointmentModel)
            .where(AppointmentModel.id == appointment_id)
            .with_for_update()
        ).first()
        if row is None:
            return None

        # Reconstruir estado actual del turno dentro del bloqueo
        appointment_entity = Appointment(
            id=row.id,
            patient_id=row.patient_id,
            professional_id=row.professional_id,
            chair_id=row.chair_id,
            service_id=row.service_id,
            start_at=row.start_at,
            end_at=row.end_at,
            status=AppointmentStatus(row.status),
        )

        # D4: Bloqueo de profesionales y sillones involucrados (anterior y nuevo)
        prof_ids = [appointment_entity.professional_id]
        if request.professional_id is not None:
            prof_ids.append(request.professional_id)
        chair_ids = [appointment_entity.chair_id]
        if request.chair_id is not None:
            chair_ids.append(request.chair_id)
        _lock_resources(session, prof_ids, chair_ids)

        new_prof_id = request.professional_id or appointment_entity.professional_id
        new_chair_id = request.chair_id or appointment_entity.chair_id

        # Cargar referencias para el nuevo destino (paciente y prestación del turno original)
        references = _load_references(
            session,
            appointment_entity.patient_id,
            new_prof_id,
            new_chair_id,
            appointment_entity.service_id,
        )
        context = _load_schedule_context(session, new_prof_id, now, tz)

        # Cargar turnos activos en rango del nuevo profesional y sillón
        search_start = request.start_at - timedelta(minutes=480)
        search_end = request.start_at + timedelta(minutes=480)
        app_repo = AppointmentRepository(session)
        prof_apps = app_repo.list_for_professional_in_range(new_prof_id, search_start, search_end)
        chair_apps = app_repo.list_for_chair_in_range(new_chair_id, search_start, search_end)
        existing_dict = {a.id: a for a in (*prof_apps, *chair_apps)}
        existing_appointments = tuple(existing_dict.values())

        orig_prof = session.get(ProfessionalModel, appointment_entity.professional_id)
        orig_prof_name = orig_prof.full_name if orig_prof is not None else ""

        result = domain_reschedule_appointment(
            appointment=appointment_entity,
            request=request,
            references=references,
            existing_appointments=existing_appointments,
            actor=actor,
            professional_name=orig_prof_name,
            context=context,
        )

        if isinstance(result, Ok):
            row.professional_id = result.appointment.professional_id
            row.chair_id = result.appointment.chair_id
            row.start_at = result.appointment.start_at
            row.end_at = result.appointment.end_at
            row.status = result.appointment.status.value
            row.updated_at = result.status_change.changed_at

            reschedule_detail = result.status_change.reschedule
            assert reschedule_detail is not None

            from_status_val = (
                result.status_change.from_status.value
                if result.status_change.from_status is not None
                else None
            )
            change_model = AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=result.appointment.id,
                from_status=from_status_val,
                to_status=result.status_change.to_status.value,
                changed_by=result.status_change.changed_by,
                changed_at=result.status_change.changed_at,
                note=None,
                reschedule_previous_start_at=reschedule_detail.previous_interval.start,
                reschedule_previous_end_at=reschedule_detail.previous_interval.end,
                reschedule_new_start_at=reschedule_detail.new_interval.start,
                reschedule_new_end_at=reschedule_detail.new_interval.end,
                reschedule_previous_professional_id=reschedule_detail.previous_professional_id,
                reschedule_new_professional_id=reschedule_detail.new_professional_id,
                reschedule_previous_chair_id=reschedule_detail.previous_chair_id,
                reschedule_new_chair_id=reschedule_detail.new_chair_id,
            )
            session.add(change_model)
            session.flush()

            if auto_commit:
                session.commit()
            return result
        else:
            session.rollback()
            return result
    except Exception:
        session.rollback()
        raise


def get_appointment_history(
    session: Session,
    appointment_id: UUID,
) -> list[HistoryEntryResponse] | None:
    app_repo = AppointmentRepository(session)
    appointment = app_repo.get_by_id(appointment_id)
    if appointment is None:
        return None

    status_repo = AppointmentStatusChangeRepository(session)
    changes = status_repo.list_by_appointment_id(appointment_id)

    user_ids = {c.changed_by for c in changes}
    names_by_id = UserRepository(session).get_display_names(user_ids)

    result: list[HistoryEntryResponse] = []
    for c in changes:
        from_val = c.from_status.value if c.from_status is not None else None
        to_val = c.to_status.value
        changed_name = names_by_id.get(c.changed_by)
        changed_at_str = format_utc_iso(c.changed_at)

        reschedule_resp: RescheduleDetailResponse | None = None
        if c.reschedule is not None:
            reschedule_resp = RescheduleDetailResponse(
                previous_start_at=format_utc_iso(c.reschedule.previous_interval.start),
                previous_end_at=format_utc_iso(c.reschedule.previous_interval.end),
                new_start_at=format_utc_iso(c.reschedule.new_interval.start),
                new_end_at=format_utc_iso(c.reschedule.new_interval.end),
                previous_professional_id=c.reschedule.previous_professional_id,
                new_professional_id=c.reschedule.new_professional_id,
                previous_chair_id=c.reschedule.previous_chair_id,
                new_chair_id=c.reschedule.new_chair_id,
            )

        result.append(
            HistoryEntryResponse(
                from_status=from_val,
                to_status=to_val,
                changed_by=c.changed_by,
                changed_by_name=changed_name,
                changed_at=changed_at_str,
                reschedule=reschedule_resp,
            )
        )
    return result
