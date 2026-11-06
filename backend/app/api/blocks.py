from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, ensure_own_professional, get_db_session, require_permission
from app.api.errors import NotFoundError
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import (
    AffectedAppointmentResponse,
    BlockCreateResponse,
    BlockInput,
    BlockResponse,
    BlocksQuery,
    format_utc_iso,
)
from app.auth.permissions import Action, Resource
from app.repositories.catalog import ProfessionalRepository
from app.services.availability import create_block, delete_block, get_block, list_blocks

router = APIRouter(tags=["Bloqueos"])


@router.get(
    "/professionals/{id}/blocks",
    status_code=status.HTTP_200_OK,
    response_model=list[BlockResponse],
    responses={**not_found_responses("Profesional"), **permission_responses()},
)
def list_blocks_endpoint(
    id: UUID,
    params: Annotated[BlocksQuery, Query()],
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.BLOCK, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> list[BlockResponse]:
    blocks = list_blocks(session, id, params.from_time, params.to_time)
    ensure_own_professional(permission, id)
    return [
        BlockResponse(
            id=b.id,
            professional_id=b.professional_id,
            start_at=format_utc_iso(b.start_at),
            end_at=format_utc_iso(b.end_at),
            reason=b.reason,
        )
        for b in blocks
    ]


@router.post(
    "/professionals/{id}/blocks",
    status_code=status.HTTP_201_CREATED,
    response_model=BlockCreateResponse,
    responses={
        **not_found_responses("Profesional"),
        **permission_responses(),
        **violation_responses(422),
    },
)
def create_block_endpoint(
    id: UUID,
    payload: BlockInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.BLOCK, Action.CREATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> BlockCreateResponse:
    prof = ProfessionalRepository(session).get_by_id(id)
    if prof is None:
        raise NotFoundError("Profesional no encontrado.")
    ensure_own_professional(permission, id)

    block, affected = create_block(
        session=session,
        professional_id=id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        reason=payload.reason,
    )

    return BlockCreateResponse(
        block=BlockResponse(
            id=block.id,
            professional_id=block.professional_id,
            start_at=format_utc_iso(block.start_at),
            end_at=format_utc_iso(block.end_at),
            reason=block.reason,
        ),
        affected_appointments=[
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


@router.delete(
    "/blocks/{block_id}",
    status_code=status.HTTP_200_OK,
    response_model=BlockResponse,
    responses={**not_found_responses("Bloqueo"), **permission_responses()},
)
def delete_block_endpoint(
    block_id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.BLOCK, Action.DELETE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> BlockResponse:
    block = get_block(session, block_id)
    ensure_own_professional(permission, block.professional_id, Resource.BLOCK, Action.DELETE)
    deleted = delete_block(session, block_id)
    return BlockResponse(
        id=deleted.id,
        professional_id=deleted.professional_id,
        start_at=format_utc_iso(deleted.start_at),
        end_at=format_utc_iso(deleted.end_at),
        reason=deleted.reason,
    )
