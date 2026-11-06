"""Servicios de aplicación para catálogos (profesionales, sillones y prestaciones).

Transaccionalidad explícita con auto_commit=True.
"""

from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.api.errors import DomainRejectedError, NotFoundError
from app.domain.model import Chair, Professional, Service
from app.domain.violations import Rejected
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ProfessionalWithLicense,
    ServiceRepository,
)


def get_professional(session: Session, identifier: UUID) -> ProfessionalWithLicense:
    repo = ProfessionalRepository(session)
    record = repo.get_with_license(identifier)
    if record is None:
        raise NotFoundError("Profesional no encontrado.")
    return record


def create_professional(
    session: Session,
    full_name: str,
    license_number: str | None = None,
    auto_commit: bool = True,
) -> ProfessionalWithLicense:
    repo = ProfessionalRepository(session)
    candidate = Professional(uuid4(), full_name, True)
    result = repo.create(candidate, license_number=license_number)
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return ProfessionalWithLicense(result.entity, license_number)


def update_professional(
    session: Session,
    identifier: UUID,
    full_name: str,
    license_number: str | None = None,
    auto_commit: bool = True,
) -> ProfessionalWithLicense:
    repo = ProfessionalRepository(session)
    existing = repo.get_with_license(identifier)
    if existing is None:
        raise NotFoundError("Profesional no encontrado.")
    candidate = Professional(identifier, full_name, existing.entity.active)
    result = repo.update(candidate, license_number=license_number)
    if result is None:
        raise NotFoundError("Profesional no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return ProfessionalWithLicense(result.entity, license_number)


def deactivate_professional(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> ProfessionalWithLicense:
    repo = ProfessionalRepository(session)
    existing = repo.get_with_license(identifier)
    if existing is None:
        raise NotFoundError("Profesional no encontrado.")
    result = repo.deactivate(identifier)
    if result is None:
        raise NotFoundError("Profesional no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return ProfessionalWithLicense(result.entity, existing.license_number)


def reactivate_professional(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> ProfessionalWithLicense:
    repo = ProfessionalRepository(session)
    existing = repo.get_with_license(identifier)
    if existing is None:
        raise NotFoundError("Profesional no encontrado.")
    result = repo.reactivate(identifier)
    if result is None:
        raise NotFoundError("Profesional no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return ProfessionalWithLicense(result.entity, existing.license_number)


def list_professionals(
    session: Session,
    active: bool | None = None,
) -> Sequence[ProfessionalWithLicense]:
    return ProfessionalRepository(session).list_with_license(active=active)


# --- Sillones ---


def get_chair(session: Session, identifier: UUID) -> Chair:
    repo = ChairRepository(session)
    row = repo.get_by_id(identifier)
    if row is None:
        raise NotFoundError("Sillón no encontrado.")
    return row


def create_chair(
    session: Session,
    name: str,
    auto_commit: bool = True,
) -> Chair:
    repo = ChairRepository(session)
    candidate = Chair(uuid4(), name, True)
    result = repo.create(candidate)
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def update_chair(
    session: Session,
    identifier: UUID,
    name: str,
    auto_commit: bool = True,
) -> Chair:
    repo = ChairRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Sillón no encontrado.")
    candidate = Chair(identifier, name, existing.active)
    result = repo.update(candidate)
    if result is None:
        raise NotFoundError("Sillón no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def deactivate_chair(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> Chair:
    repo = ChairRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Sillón no encontrado.")
    result = repo.deactivate(identifier)
    if result is None:
        raise NotFoundError("Sillón no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def reactivate_chair(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> Chair:
    repo = ChairRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Sillón no encontrado.")
    result = repo.reactivate(identifier)
    if result is None:
        raise NotFoundError("Sillón no encontrado.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def list_chairs(
    session: Session,
    active: bool | None = None,
) -> Sequence[Chair]:
    return ChairRepository(session).list(active=active)


# --- Prestaciones ---


def get_service(session: Session, identifier: UUID) -> Service:
    repo = ServiceRepository(session)
    row = repo.get_by_id(identifier)
    if row is None:
        raise NotFoundError("Prestación no encontrada.")
    return row


def create_service(
    session: Session,
    name: str,
    default_duration_min: int,
    auto_commit: bool = True,
) -> Service:
    repo = ServiceRepository(session)
    candidate = Service(uuid4(), name, default_duration_min, True)
    result = repo.create(candidate)
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def update_service(
    session: Session,
    identifier: UUID,
    name: str,
    default_duration_min: int,
    auto_commit: bool = True,
) -> Service:
    repo = ServiceRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Prestación no encontrada.")
    candidate = Service(identifier, name, default_duration_min, existing.active)
    result = repo.update(candidate)
    if result is None:
        raise NotFoundError("Prestación no encontrada.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def deactivate_service(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> Service:
    repo = ServiceRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Prestación no encontrada.")
    result = repo.deactivate(identifier)
    if result is None:
        raise NotFoundError("Prestación no encontrada.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def reactivate_service(
    session: Session,
    identifier: UUID,
    auto_commit: bool = True,
) -> Service:
    repo = ServiceRepository(session)
    existing = repo.get_by_id(identifier)
    if existing is None:
        raise NotFoundError("Prestación no encontrada.")
    result = repo.reactivate(identifier)
    if result is None:
        raise NotFoundError("Prestación no encontrada.")
    if isinstance(result, Rejected):
        raise DomainRejectedError(result)
    if auto_commit:
        session.commit()
    return result.entity


def list_services(
    session: Session,
    active: bool | None = None,
) -> Sequence[Service]:
    return ServiceRepository(session).list(active=active)
