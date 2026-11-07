from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.openapi import permission_responses
from app.api.schemas import (
    AgendaAppointmentResponse,
    AgendaQuery,
    AgendaResponse,
    AgendaWorkingHoursResponse,
    BlockResponse,
    format_utc_iso,
)
from app.auth.permissions import Action, Resource
from app.config import Settings
from app.services.agenda import AgendaAppointment, get_agenda

router = APIRouter(prefix="/agenda", tags=["Agenda"])


def to_agenda_appointment_response(item: AgendaAppointment) -> AgendaAppointmentResponse:
    return AgendaAppointmentResponse(
        id=item.id,
        patient_id=item.patient_id,
        patient_name=item.patient_name,
        professional_id=item.professional_id,
        professional_name=item.professional_name,
        chair_id=item.chair_id,
        chair_name=item.chair_name,
        service_id=item.service_id,
        service_name=item.service_name,
        start_at=format_utc_iso(item.start_at),
        end_at=format_utc_iso(item.end_at),
        status=item.status,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=AgendaResponse,
    responses={**permission_responses()},
)
def get_agenda_endpoint(
    params: Annotated[AgendaQuery, Query()],
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.APPOINTMENT, Action.READ_AGENDA)),
    ],
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> AgendaResponse:
    settings: Settings = request.app.state.settings
    agenda = get_agenda(
        session,
        params.from_date,
        params.to_date,
        params.professional_id,
        params.chair_id,
        ZoneInfo(settings.app_timezone),
    )
    return AgendaResponse(
        from_date=agenda.from_date,
        to_date=agenda.to_date,
        timezone=agenda.timezone,
        appointments=[to_agenda_appointment_response(item) for item in agenda.appointments],
        working_hours=[
            AgendaWorkingHoursResponse(
                professional_id=slot.professional_id,
                weekday=slot.weekday,
                start=f"{slot.start_minute // 60:02d}:{slot.start_minute % 60:02d}",
                end=f"{slot.end_minute // 60:02d}:{slot.end_minute % 60:02d}",
            )
            for slot in agenda.working_hours
        ],
        blocks=[
            BlockResponse(
                id=block.id,
                professional_id=block.professional_id,
                start_at=format_utc_iso(block.start_at),
                end_at=format_utc_iso(block.end_at),
                reason=block.reason,
            )
            for block in agenda.blocks
        ],
    )
