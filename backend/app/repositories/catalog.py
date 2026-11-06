from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.catalog.activation import deactivate, reactivate
from app.domain.catalog.create import create_chair, create_professional, create_service
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.catalog.update import update_chair, update_professional, update_service
from app.domain.model import Chair, Professional, Service
from app.domain.violations import Rejected, Violation, ViolationCode
from app.db.models import ChairModel, ProfessionalModel, ServiceModel
from app.repositories._integrity import constraint_name


@dataclass(frozen=True, slots=True)
class ProfessionalWithLicense:
    entity: Professional
    license_number: str | None = None



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

    def create(
        self, candidate: Professional, license_number: str | None = None
    ) -> CatalogResult[Professional]:
        result = create_professional(candidate)
        if isinstance(result, Rejected):
            return result
        row = ProfessionalModel(
            id=result.entity.id,
            full_name=result.entity.full_name,
            active=result.entity.active,
            license_number=license_number,
        )
        self._session.add(row)
        self._session.flush()
        return Ok(result.entity)

    def update(
        self, candidate: Professional, license_number: str | None = None
    ) -> CatalogResult[Professional] | None:
        row = self._session.get(ProfessionalModel, candidate.id)
        if row is None:
            return None
        result = update_professional(candidate)
        if isinstance(result, Rejected):
            return result
        row.full_name = result.entity.full_name
        row.license_number = license_number
        self._session.flush()
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Professional | None:
        row = self._session.get(ProfessionalModel, identifier)
        return None if row is None else Professional(row.id, row.full_name, row.active)

    def get_with_license(self, identifier: UUID) -> ProfessionalWithLicense | None:
        row = self._session.get(ProfessionalModel, identifier)
        if row is None:
            return None
        return ProfessionalWithLicense(
            Professional(row.id, row.full_name, row.active),
            row.license_number,
        )

    def list(self, active: bool | None = None) -> Sequence[Professional]:
        stmt = select(ProfessionalModel)
        if active is not None:
            stmt = stmt.where(ProfessionalModel.active == active)
        rows = self._session.scalars(
            stmt.order_by(func.lower(ProfessionalModel.full_name).asc(), ProfessionalModel.id.asc())
        ).all()
        return [Professional(row.id, row.full_name, row.active) for row in rows]

    def list_with_license(
        self, active: bool | None = None
    ) -> Sequence[ProfessionalWithLicense]:
        stmt = select(ProfessionalModel)
        if active is not None:
            stmt = stmt.where(ProfessionalModel.active == active)
        rows = self._session.scalars(
            stmt.order_by(func.lower(ProfessionalModel.full_name).asc(), ProfessionalModel.id.asc())
        ).all()
        return [
            ProfessionalWithLicense(
                Professional(row.id, row.full_name, row.active),
                row.license_number,
            )
            for row in rows
        ]

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

    def update(self, candidate: Chair) -> CatalogResult[Chair] | None:
        row = self._session.get(ChairModel, candidate.id)
        if row is None:
            return None
        result = update_chair(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        row.name = result.entity.name
        row.name_normalized = _normalized_name(result.entity.name)
        try:
            with self._session.begin_nested():
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_chair_name_normalized":
                return _duplicate_name(result.entity.name, "un sillón")
            raise
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Chair | None:
        row = self._session.get(ChairModel, identifier)
        return None if row is None else Chair(row.id, row.name, row.active)

    def list(self, active: bool | None = None) -> Sequence[Chair]:
        stmt = select(ChairModel)
        if active is not None:
            stmt = stmt.where(ChairModel.active == active)
        rows = self._session.scalars(
            stmt.order_by(ChairModel.name_normalized.asc(), ChairModel.id.asc())
        ).all()
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

    def update(self, candidate: Service) -> CatalogResult[Service] | None:
        row = self._session.get(ServiceModel, candidate.id)
        if row is None:
            return None
        result = update_service(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        row.name = result.entity.name
        row.name_normalized = _normalized_name(result.entity.name)
        row.default_duration_min = result.entity.default_duration_min
        try:
            with self._session.begin_nested():
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_service_name_normalized":
                return _duplicate_name(result.entity.name, "una prestación")
            raise
        return Ok(result.entity)

    def get_by_id(self, identifier: UUID) -> Service | None:
        row = self._session.get(ServiceModel, identifier)
        return None if row is None else Service(row.id, row.name, row.default_duration_min, row.active)

    def list(self, active: bool | None = None) -> Sequence[Service]:
        stmt = select(ServiceModel)
        if active is not None:
            stmt = stmt.where(ServiceModel.active == active)
        rows = self._session.scalars(
            stmt.order_by(ServiceModel.name_normalized.asc(), ServiceModel.id.asc())
        ).all()
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
