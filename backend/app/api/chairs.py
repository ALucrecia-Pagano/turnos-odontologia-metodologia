from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import ChairInput, ChairResponse
from app.auth.permissions import Action, Resource
from app.services.catalog import (
    create_chair,
    deactivate_chair,
    get_chair,
    list_chairs,
    reactivate_chair,
    update_chair,
)

router = APIRouter(prefix="/chairs", tags=["Sillones"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ChairResponse,
    responses={**violation_responses(409, 422), **permission_responses()},
)
def create_chair_endpoint(
    payload: ChairInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.CREATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ChairResponse:
    chair = create_chair(session, payload.name)
    return ChairResponse(id=chair.id, name=chair.name, active=chair.active)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ChairResponse],
    responses={**permission_responses()},
)
def list_chairs_endpoint(
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
    active: Annotated[bool | None, Query()] = None,
) -> list[ChairResponse]:
    chairs = list_chairs(session, active=active)
    return [ChairResponse(id=c.id, name=c.name, active=c.active) for c in chairs]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ChairResponse,
    responses={**not_found_responses("Sillón"), **permission_responses()},
)
def get_chair_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ChairResponse:
    chair = get_chair(session, id)
    return ChairResponse(id=chair.id, name=chair.name, active=chair.active)


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=ChairResponse,
    responses={
        **violation_responses(409, 422),
        **not_found_responses("Sillón"),
        **permission_responses(),
    },
)
def update_chair_endpoint(
    id: UUID,
    payload: ChairInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ChairResponse:
    chair = update_chair(session, id, payload.name)
    return ChairResponse(id=chair.id, name=chair.name, active=chair.active)


@router.post(
    "/{id}/deactivate",
    status_code=status.HTTP_200_OK,
    response_model=ChairResponse,
    responses={**not_found_responses("Sillón"), **permission_responses()},
)
def deactivate_chair_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.DELETE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ChairResponse:
    chair = deactivate_chair(session, id)
    return ChairResponse(id=chair.id, name=chair.name, active=chair.active)


@router.post(
    "/{id}/reactivate",
    status_code=status.HTTP_200_OK,
    response_model=ChairResponse,
    responses={**not_found_responses("Sillón"), **permission_responses()},
)
def reactivate_chair_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.CHAIR, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> ChairResponse:
    chair = reactivate_chair(session, id)
    return ChairResponse(id=chair.id, name=chair.name, active=chair.active)
