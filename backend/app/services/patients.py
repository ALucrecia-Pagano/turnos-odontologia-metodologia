"""Servicios de aplicación para pacientes.

Transaccionalidad explícita con auto_commit=True.
"""

from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.api.errors import DomainRejectedError, NotFoundError
from app.domain.model import Patient
from app.domain.violations import Rejected
from app.repositories.patients import PatientRepository


def get_patient(session: Session, identifier: UUID) -> Patient:
    repo = PatientRepository(session)
    row = repo.get_by_id(identifier)
    if row is None:
        raise NotFoundError("Paciente no encontrado.")
    return row


def create_patient(
    session: Session,
    full_name: str,
    dni: str,
    phone: str | None = None,
    health_insurance: str | None = None,
    auto_commit: bool = True,
) -> Patient:
    repo = PatientRepository(session)
    candidate = Patient(uuid4(), full_name, dni, phone, health_insurance)
    result = repo.create(candidate)
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def update_patient(
    session: Session,
    identifier: UUID,
    full_name: str,
    dni: str,
    phone: str | None = None,
    health_insurance: str | None = None,
    auto_commit: bool = True,
) -> Patient:
    repo = PatientRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Paciente no encontrado.")
    candidate = Patient(identifier, full_name, dni, phone, health_insurance)
    result = repo.update(candidate)
    if result is None:
        raise NotFoundError("Paciente no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def list_patients(
    session: Session,
    query: str | None = None,
) -> Sequence[Patient]:
    return PatientRepository(session).list(query=query)
