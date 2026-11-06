from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import ProfessionalInput, ProfessionalResponse
from app.auth.permissions import Action, Resource
from app.services.catalog import (
    create_professional,
    deactivate_professional,
    get_professional,
    list_professionals,
    reactivate_professional,
    update_professional,
)

router = APIRouter(prefix="/professionals", tags=["Profesionales"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfessionalResponse,
    responses={**violation_responses(422), **permission_responses()},
)
def create_professional_endpoint(
    payload: ProfessionalInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.CREATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfessionalResponse:
    record = create_professional(
        session,
        payload.full_name,
        license_number=payload.license_number,
    )
    return ProfessionalResponse(
        id=record.entity.id,
        full_name=record.entity.full_name,
        active=record.entity.active,
        license_number=record.license_number,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ProfessionalResponse],
    responses={**permission_responses()},
)
def list_professionals_endpoint(
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
    active: Annotated[bool | None, Query()] = None,
) -> list[ProfessionalResponse]:
    records = list_professionals(session, active=active)
    return [
        ProfessionalResponse(
            id=r.entity.id,
            full_name=r.entity.full_name,
            active=r.entity.active,
            license_number=r.license_number,
        )
        for r in records
    ]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ProfessionalResponse,
    responses={**not_found_responses("Profesional"), **permission_responses()},
)
def get_professional_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfessionalResponse:
    record = get_professional(session, id)
    return ProfessionalResponse(
        id=record.entity.id,
        full_name=record.entity.full_name,
        active=record.entity.active,
        license_number=record.license_number,
    )


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ProfessionalResponse,
    responses={
        **violation_responses(422),
        **not_found_responses("Profesional"),
        **permission_responses(),
    },
)
def update_professional_endpoint(
    id: UUID,
    payload: ProfessionalInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfessionalResponse:
    record = update_professional(
        session,
        id,
        payload.full_name,
        license_number=payload.license_number,
    )
    return ProfessionalResponse(
        id=record.entity.id,
        full_name=record.entity.full_name,
        active=record.entity.active,
        license_number=record.license_number,
    )


@router.post(
    "/{id}/deactivate",
    status_code=status.HTTP_200_OK,
    response_model=ProfessionalResponse,
    responses={**not_found_responses("Profesional"), **permission_responses()},
)
def deactivate_professional_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.DELETE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfessionalResponse:
    record = deactivate_professional(session, id)
    return ProfessionalResponse(
        id=record.entity.id,
        full_name=record.entity.full_name,
        active=record.entity.active,
        license_number=record.license_number,
    )


@router.post(
    "/{id}/reactivate",
    status_code=status.HTTP_200_OK,
    response_model=ProfessionalResponse,
    responses={**not_found_responses("Profesional"), **permission_responses()},
)
def reactivate_professional_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PROFESSIONAL, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ProfessionalResponse:
    record = reactivate_professional(session, id)
    return ProfessionalResponse(
        id=record.entity.id,
        full_name=record.entity.full_name,
        active=record.entity.active,
        license_number=record.license_number,
    )
