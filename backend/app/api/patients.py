from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Permission, get_db_session, require_permission
from app.api.openapi import not_found_responses, permission_responses, violation_responses
from app.api.schemas import PatientInput, PatientResponse
from app.auth.permissions import Action, Resource
from app.services.patients import (
    create_patient,
    get_patient,
    list_patients,
    update_patient,
)

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PatientResponse,
    responses={**violation_responses(409, 422), **permission_responses()},
)
def create_patient_endpoint(
    payload: PatientInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PATIENT, Action.CREATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> PatientResponse:
    patient = create_patient(
        session,
        payload.full_name,
        payload.dni,
        phone=payload.phone,
        health_insurance=payload.health_insurance,
    )
    return PatientResponse(
        id=patient.id,
        full_name=patient.full_name,
        dni=patient.dni,
        phone=patient.phone,
        health_insurance=patient.health_insurance,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PatientResponse],
    responses={**permission_responses()},
)
def list_patients_endpoint(
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PATIENT, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
    query: Annotated[str | None, Query()] = None,
) -> list[PatientResponse]:
    patients = list_patients(session, query=query)
    return [
        PatientResponse(
            id=p.id,
            full_name=p.full_name,
            dni=p.dni,
            phone=p.phone,
            health_insurance=p.health_insurance,
        )
        for p in patients
    ]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=PatientResponse,
    responses={**not_found_responses("Paciente"), **permission_responses()},
)
def get_patient_endpoint(
    id: UUID,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PATIENT, Action.READ)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> PatientResponse:
    patient = get_patient(session, id)
    return PatientResponse(
        id=patient.id,
        full_name=patient.full_name,
        dni=patient.dni,
        phone=patient.phone,
        health_insurance=patient.health_insurance,
    )


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=PatientResponse,
    responses={
        **violation_responses(409, 422),
        **not_found_responses("Paciente"),
        **permission_responses(),
    },
)
def update_patient_endpoint(
    id: UUID,
    payload: PatientInput,
    permission: Annotated[
        Permission,
        Depends(require_permission(Resource.PATIENT, Action.UPDATE)),
    ],
    session: Annotated[Session, Depends(get_db_session)],
) -> PatientResponse:
    patient = update_patient(
        session,
        id,
        payload.full_name,
        payload.dni,
        phone=payload.phone,
        health_insurance=payload.health_insurance,
    )
    return PatientResponse(
        id=patient.id,
        full_name=patient.full_name,
        dni=patient.dni,
        phone=patient.phone,
        health_insurance=patient.health_insurance,
    )
