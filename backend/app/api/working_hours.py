from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, ensure_own_professional, get_db_session, require_permission
from app.api.errors import NotFoundError
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import (
    AffectedAppointmentResponse,
    WorkingHoursResponse,
    WorkingHoursSlotInput,
    WorkingHoursSlotResponse,
    format_utc_iso,
)
from app.auth.permissions import Action, Resource
from app.domain.model import WorkingHours
from app.repositories.catalog import ProfessionalRepository
from app.services.availability import get_working_hours, replace_working_hours

router = APIRouter(prefix="/professionals", tags=["Horarios"])


@router.get(
    "/{id}/working-hours",
    status_code=status.HTTP_200_OK,
    response_model=list[WorkingHoursSlotResponse],
    responses={**not_found_responses("Profesional"), **permission_responses()},
)
def get_working_hours_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.WORKING_HOURS, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[WorkingHoursSlotResponse]:
    slots = get_working_hours(session, id)
    ensure_own_professional(permission, id)
    return [
        WorkingHoursSlotResponse(
            weekday=slot.weekday,
            start=f"{slot.start_minute // 60:02d}:{slot.start_minute % 60:02d}",
            end=f"{slot.end_minute // 60:02d}:{slot.end_minute % 60:02d}",
        )
        for slot in slots
    ]


@router.put(
    "/{id}/working-hours",
    status_code=status.HTTP_200_OK,
    response_model=WorkingHoursResponse,
    responses={
        **not_found_responses("Profesional"),
        **permission_responses(),
        **violation_responses(422),
    },
)
def replace_working_hours_endpoint(
    id: UUID,
    slots_input: list[WorkingHoursSlotInput],
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.WORKING_HOURS, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
    request: Request,
) -> WorkingHoursResponse:
    prof = ProfessionalRepository(session).get_by_id(id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")
    ensure_own_professional(permission, id)

    domain_slots: list[WorkingHours] = []
    for s in slots_input:
        start_h, start_m = map(int, s.start.split(":"))
        end_h, end_m = map(int, s.end.split(":"))
        domain_slots.append(
            WorkingHours(
                professional_id=id,
                weekday=s.weekday,
                start_minute=start_h * 60 + start_m,
                end_minute=end_h * 60 + end_m,
            )
        )

    now_utc = datetime.now(timezone.utc)
    app_tz_name = getattr(request.app.state.settings, "app_timezone", "America/Argentina/Buenos_Aires")
    tz = ZoneInfo(app_tz_name)
    saved_slots, affected = replace_working_hours(session, id, domain_slots, now_utc, tz)

    return WorkingHoursResponse(
        working_hours=[
            WorkingHoursSlotResponse(
                weekday=slot.weekday,
                start=f"{slot.start_minute // 60:02d}:{slot.start_minute % 60:02d}",
                end=f"{slot.end_minute // 60:02d}:{slot.end_minute % 60:02d}",
            )
            for slot in saved_slots
        ],
        appointments_outside_hours=[
            AffectedAppointmentResponse(
                id=apt.id,
                patient_id=apt.patient_id,
                patient_name=apt.patient_name,
                chair_id=apt.chair_id,
                start_at=format_utc_iso(apt.start_at),
                end_at=format_utc_iso(apt.end_at),
                status=apt.status,
            )
            for apt in affected
        ],
    )
