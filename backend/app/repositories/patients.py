from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import PatientModel
from app.domain.catalog.create import create_patient
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.catalog.update import update_patient
from app.domain.model import Patient
from app.domain.violations import Rejected, Violation, ViolationCode
from app.repositories._integrity import constraint_name


class PatientRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, candidate: Patient) -> CatalogResult[Patient]:
        result = create_patient(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        entity = result.entity
        row = PatientModel(
            id=entity.id,
            full_name=entity.full_name,
            dni=entity.dni,
            phone=entity.phone,
            health_insurance=entity.health_insurance,
        )
        try:
            with self._session.begin_nested():
                self._session.add(row)
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_patient_dni":
                digits = entity.dni
                shown = f"{digits[:-6]}.{digits[-6:-3]}.{digits[-3:]}"
                return Rejected(
                    (
                        Violation(
                            ViolationCode.DUPLICATE_DNI,
                            f"Ya existe un paciente con el DNI {shown}.",
                        ),
                    )
                )
            raise
        return Ok(entity)

    def update(self, candidate: Patient) -> CatalogResult[Patient] | None:
        row = self._session.get(PatientModel, candidate.id)
        if row is None:
            return None
        result = update_patient(candidate, self.list())
        if isinstance(result, Rejected):
            return result
        entity = result.entity
        row.full_name = entity.full_name
        row.dni = entity.dni
        row.phone = entity.phone
        row.health_insurance = entity.health_insurance
        try:
            with self._session.begin_nested():
                self._session.flush()
        except IntegrityError as error:
            if constraint_name(error) == "ux_patient_dni":
                digits = entity.dni
                shown = f"{digits[:-6]}.{digits[-6:-3]}.{digits[-3:]}"
                return Rejected(
                    (
                        Violation(
                            ViolationCode.DUPLICATE_DNI,
                            f"Ya existe un paciente con el DNI {shown}.",
                        ),
                    )
                )
            raise
        return Ok(entity)

    def get_by_id(self, identifier: UUID) -> Patient | None:
        row = self._session.get(PatientModel, identifier)
        return None if row is None else self._to_domain(row)

    def list(self, query: str | None = None) -> Sequence[Patient]:
        stmt = select(PatientModel)
        if query:
            q = query.strip()
            if q:
                escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                clauses: list[ColumnElement[bool]] = [PatientModel.full_name.ilike(f"%{escaped}%", escape="\\")]
                digits = "".join(ch for ch in q if ch.isdigit())
                if digits:
                    clauses.append(PatientModel.dni.startswith(digits))
                stmt = stmt.where(or_(*clauses))
        rows = self._session.scalars(
            stmt.order_by(func.lower(PatientModel.full_name).asc(), PatientModel.id.asc())
        ).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: PatientModel) -> Patient:
        return Patient(row.id, row.full_name, row.dni, row.phone, row.health_insurance)
