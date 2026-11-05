from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.catalog.activation import deactivate, reactivate
from app.domain.catalog.create import create_chair, create_professional, create_service
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import Chair, Professional, Service
from app.domain.violations import Rejected, Violation, ViolationCode
from app.db.models import ChairModel, ProfessionalModel, ServiceModel
from app.repositories._integrity import constraint_name


def _normalized_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def _duplicate_name(name: str, subject: str) -> Rejected:
    display_name = " ".join(name.split())
    return Rejected(
        (
            Violation(
                ViolationCode.DUPLICATE_NAME,
                f'Ya existe {subject} con el nombre "{display_name}".',
            ),
        )
    )


class ProfessionalRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, candidate: Professional) -> CatalogResult[Professional]:
        result = create_professional(candidate)
        if isinstance(result, Rejected):
            return result
        row = ProfessionalModel(
            id=result.entity.id,
            full_name=result.entity.full_name,
            active=result.entity.active,
        )
        self._session.add(row)
        self._session.flush()
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Professional | None:
        row = self._session.get(ProfessionalModel, identifier)
        return None if row is None else Professional(row.id, row.full_name, row.active)

    def list(self) -> Sequence[Professional]:
        rows = self._session.scalars(select(ProfessionalModel).order_by(ProfessionalModel.id)).all()
        return [Professional(row.id, row.full_name, row.active) for row in rows]

    def deactivate(self, identifier: UUID) -> CatalogResult[Professional] | None:
        return self._set_active(identifier, False)

    def reactivate(self, identifier: UUID) -> CatalogResult[Professional] | None:
        return self._set_active(identifier, True)

    def _set_active(self, identifier: UUID, active: bool) -> CatalogResult[Professional] | None:
        row = self._session.get(ProfessionalModel, identifier)
        if row is None:
            return None
        entity = Professional(row.id, row.full_name, row.active)
        changed = reactivate(entity) if active else deactivate(entity)
        row.active = changed.active
        self._session.flush()
        return Ok(changed)


class ChairRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, candidate: Chair) -> CatalogResult[Chair]:
        result = create_chair(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        row = ChairModel(
            id=result.entity.id,
            name=result.entity.name,
            name_normalized=_normalized_name(result.entity.name),
            active=result.entity.active,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_chair_name_normalized":
                return _duplicate_name(result.entity.name, "un sillón")
            raise
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Chair | None:
        row = self._session.get(ChairModel, identifier)
        return None if row is None else Chair(row.id, row.name, row.active)

    def list(self) -> Sequence[Chair]:
        rows = self._session.scalars(select(ChairModel).order_by(ChairModel.id)).all()
        return [Chair(row.id, row.name, row.active) for row in rows]

    def deactivate(self, identifier: UUID) -> CatalogResult[Chair] | None:
        return self._set_active(identifier, False)

    def reactivate(self, identifier: UUID) -> CatalogResult[Chair] | None:
        return self._set_active(identifier, True)

    def _set_active(self, identifier: UUID, active: bool) -> CatalogResult[Chair] | None:
        row = self._session.get(ChairModel, identifier)
        if row is None:
            return None
        entity = Chair(row.id, row.name, row.active)
        changed = reactivate(entity) if active else deactivate(entity)
        row.active = changed.active
        self._session.flush()
        return Ok(changed)


class ServiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, candidate: Service) -> CatalogResult[Service]:
        result = create_service(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        row = ServiceModel(
            id=result.entity.id,
            name=result.entity.name,
            name_normalized=_normalized_name(result.entity.name),
            default_duration_min=result.entity.default_duration_min,
            active=result.entity.active,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_service_name_normalized":
                return _duplicate_name(result.entity.name, "una prestación")
            raise
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Service | None:
        row = self._session.get(ServiceModel, identifier)
        return None if row is None else Service(row.id, row.name, row.default_duration_min, row.active)

    def list(self) -> Sequence[Service]:
        rows = self._session.scalars(select(ServiceModel).order_by(ServiceModel.id)).all()
        return [
            Service(row.id, row.name, row.default_duration_min, row.active)
            for row in rows
        ]

    def deactivate(self, identifier: UUID) -> CatalogResult[Service] | None:
        return self._set_active(identifier, False)

    def reactivate(self, identifier: UUID) -> CatalogResult[Service] | None:
        return self._set_active(identifier, True)

    def _set_active(self, identifier: UUID, active: bool) -> CatalogResult[Service] | None:
        row = self._session.get(ServiceModel, identifier)
        if row is None:
            return None
        entity = Service(row.id, row.name, row.default_duration_min, row.active)
        changed = reactivate(entity) if active else deactivate(entity)
        row.active = changed.active
        self._session.flush()
        return Ok(changed)
