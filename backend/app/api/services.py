from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import ServiceInput, ServiceResponse
from app.auth.permissions import Action, Resource
from app.services.catalog import (
    create_service,
    deactivate_service,
    get_service,
    list_services,
    reactivate_service,
    update_service,
)

router = APIRouter(prefix="/services", tags=["Prestaciones"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ServiceResponse,
    responses={**violation_responses(409, 422), **permission_responses()},
)
def create_service_endpoint(
    payload: ServiceInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.CREATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ServiceResponse:
    service = create_service(session, payload.name, payload.default_duration_min)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        default_duration_min=service.default_duration_min,
        active=service.active,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ServiceResponse],
    responses={**permission_responses()},
)
def list_services_endpoint(
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
    active: Annotated[bool | None, Query()] = None,
) -> list[ServiceResponse]:
    services = list_services(session, active=active)
    return [
        ServiceResponse(
            id=s.id,
            name=s.name,
            default_duration_min=s.default_duration_min,
            active=s.active,
        )
        for s in services
    ]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ServiceResponse,
    responses={**not_found_responses("Prestación"), **permission_responses()},
)
def get_service_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ServiceResponse:
    service = get_service(session, id)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        default_duration_min=service.default_duration_min,
        active=service.active,
    )


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ServiceResponse,
    responses={
        **violation_responses(409, 422),
        **not_found_responses("Prestación"),
        **permission_responses(),
    },
)
def update_service_endpoint(
    id: UUID,
    payload: ServiceInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ServiceResponse:
    service = update_service(
        session, id, payload.name, payload.default_duration_min
    )
    return ServiceResponse(
        id=service.id,
        name=service.name,
        default_duration_min=service.default_duration_min,
        active=service.active,
    )


@router.post(
    "/{id}/deactivate",
    status_code=status.HTTP_200_OK,
    response_model=ServiceResponse,
    responses={**not_found_responses("Prestación"), **permission_responses()},
)
def deactivate_service_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.DELETE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ServiceResponse:
    service = deactivate_service(session, id)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        default_duration_min=service.default_duration_min,
        active=service.active,
    )


@router.post(
    "/{id}/reactivate",
    status_code=status.HTTP_200_OK,
    response_model=ServiceResponse,
    responses={**not_found_responses("Prestación"), **permission_responses()},
)
def reactivate_service_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.SERVICE, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ServiceResponse:
    service = reactivate_service(session, id)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        default_duration_min=service.default_duration_min,
        active=service.active,
    )
