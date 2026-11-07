from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.errors import DomainRejectedError
from app.api.openapi import permission_responses, violation_responses
from app.api.schemas import AppointmentInput, AppointmentResponse, format_utc_iso
from app.auth.permissions import Action, Resource
from app.config import Settings
from app.domain.model import NewAppointmentRequest
from app.domain.violations import Ok, Rejected
from app.services.appointments import book_appointment

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
