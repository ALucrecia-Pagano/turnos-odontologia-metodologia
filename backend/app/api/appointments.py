from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.agenda import to_agenda_appointment_response
from app.api.deps import Permission, ensure_own_professional, get_db_session, require_permission
from app.api.errors import DomainRejectedError, NotFoundError
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import (
    AgendaAppointmentResponse,
    AppointmentInput,
    AppointmentResponse,
    HistoryEntryResponse,
    RescheduleInput,
    StatusChangeInput,
    format_utc_iso,
)
from app.auth.permissions import Action, Resource, Scope
from app.config import Settings
from app.domain.model import AppointmentStatus, NewAppointmentRequest, RescheduleRequest
from app.domain.violations import Ok, Rejected
from app.repositories.appointment import AppointmentRepository
from app.services.agenda import get_agenda_appointment
from app.services.appointments import (
    book_appointment,
    cancel_appointment,
    change_appointment_status,
    get_appointment_history,
    reschedule_appointment,
)

router = APIRouter(prefix="/appointments", tags=["Turnos"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AppointmentResponse,
    responses={
        **violation_responses(409, 422),
        **permission_responses(),
    },
)
def create_appointment_endpoint(
    body: AppointmentInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.CREATE)),
    ],
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> AppointmentResponse:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    tz = ZoneInfo(settings.app_timezone)

    appointment_req = NewAppointmentRequest(
        id=uuid4(),
        patient_id=body.patient_id,
        professional_id=body.professional_id,
        chair_id=body.chair_id,
        service_id=body.service_id,
        start_at=body.start_at,
        duration_min=body.duration_min,
        changed_by=permission.actor.user_id,
    )

    result = book_appointment(
        session=session,
        request=appointment_req,
        now=now,
        tz=tz,
        auto_commit=True,
    )

    if isinstance(result, Rejected):
        raise DomainRejectedError(result)

    assert isinstance(result, Ok)
    appointment = result.appointment
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        professional_id=appointment.professional_id,
        chair_id=appointment.chair_id,
        service_id=appointment.service_id,
        start_at=format_utc_iso(appointment.interval.start),
        end_at=format_utc_iso(appointment.interval.end),
        status=appointment.status.value,
    )


@router.post(
    "/{id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    responses={
        **violation_responses(422),
        **not_found_responses("Turno"),
        **permission_responses(),
    },
)
def cancel_appointment_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.CANCEL)),
    ],
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> AppointmentResponse:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    tz = ZoneInfo(settings.app_timezone)

    result = cancel_appointment(
        session=session,
        appointment_id=id,
        actor=permission.actor,
        now=now,
        tz=tz,
        auto_commit=True,
    )

    if result is None:
        raise NotFoundError("Turno no encontrado.")

    if isinstance(result, Rejected):
        raise DomainRejectedError(result)

    assert isinstance(result, Ok)
    appointment = result.appointment
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        professional_id=appointment.professional_id,
        chair_id=appointment.chair_id,
        service_id=appointment.service_id,
        start_at=format_utc_iso(appointment.interval.start),
        end_at=format_utc_iso(appointment.interval.end),
        status=appointment.status.value,
    )


@router.post(
    "/{id}/reschedule",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    responses={
        **violation_responses(409, 422),
        **not_found_responses("Turno"),
        **permission_responses(),
    },
)
def reschedule_appointment_endpoint(
    id: UUID,
    body: RescheduleInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.RESCHEDULE)),
    ],
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> AppointmentResponse:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    tz = ZoneInfo(settings.app_timezone)

    reschedule_req = RescheduleRequest(
        start_at=body.start_at,
        professional_id=body.professional_id,
        chair_id=body.chair_id,
        duration_min=body.duration_min,
    )

    result = reschedule_appointment(
        session=session,
        appointment_id=id,
        request=reschedule_req,
        actor=permission.actor,
        now=now,
        tz=tz,
        auto_commit=True,
    )

    if result is None:
        raise NotFoundError("Turno no encontrado.")

    if isinstance(result, Rejected):
        raise DomainRejectedError(result)

    assert isinstance(result, Ok)
    appointment = result.appointment
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        professional_id=appointment.professional_id,
        chair_id=appointment.chair_id,
        service_id=appointment.service_id,
        start_at=format_utc_iso(appointment.interval.start),
        end_at=format_utc_iso(appointment.interval.end),
        status=appointment.status.value,
    )


@router.post(
    "/{id}/status",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    responses={
        **violation_responses(422),
        **not_found_responses("Turno"),
        **permission_responses(),
    },
)
def change_appointment_status_endpoint(
    id: UUID,
    body: StatusChangeInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.CHANGE_STATUS)),
    ],
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> AppointmentResponse:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    tz = ZoneInfo(settings.app_timezone)

    result = change_appointment_status(
        session=session,
        appointment_id=id,
        target_status=AppointmentStatus(body.to_status),
        actor=permission.actor,
        now=now,
        tz=tz,
        auto_commit=True,
    )

    if result is None:
        raise NotFoundError("Turno no encontrado.")

    if isinstance(result, Rejected):
        raise DomainRejectedError(result)

    assert isinstance(result, Ok)
    appointment = result.appointment
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        professional_id=appointment.professional_id,
        chair_id=appointment.chair_id,
        service_id=appointment.service_id,
        start_at=format_utc_iso(appointment.interval.start),
        end_at=format_utc_iso(appointment.interval.end),
        status=appointment.status.value,
    )


@router.get(
    "/{id}/history",
    status_code=status.HTTP_200_OK,
    response_model=list[HistoryEntryResponse],
    responses={
        **not_found_responses("Turno"),
        **permission_responses(),
    },
)
def get_appointment_history_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT_HISTORY, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[HistoryEntryResponse]:
    appointment = AppointmentRepository(session).get_by_id(id)
    if appointment is None:
        raise NotFoundError("Turno no encontrado.")

    if permission.scope is Scope.OWN:
        ensure_own_professional(permission, appointment.professional_id)

    history = get_appointment_history(session, id)
    if history is None:
        raise NotFoundError("Turno no encontrado.")

    return history


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=AgendaAppointmentResponse,
    responses={
        **not_found_responses("Turno"),
        **permission_responses(),
    },
)
def get_appointment_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.READ_AGENDA)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> AgendaAppointmentResponse:
    appointment = get_agenda_appointment(session, id)
    if appointment is None:
        raise NotFoundError("Turno no encontrado.")
    return to_agenda_appointment_response(appointment)
