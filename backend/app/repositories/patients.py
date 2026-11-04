from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import PatientModel
from app.domain.catalog.create import create_patient
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import Patient
from app.domain.violations import Rejected, Violation, ViolationCode


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


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
            if _constraint_name(error) == "ux_patient_dni":
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

    def list(self) -> Sequence[Patient]:
        rows = self._session.scalars(select(PatientModel).order_by(PatientModel.id)).all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: PatientModel) -> Patient:
        return Patient(row.id, row.full_name, row.dni, row.phone, row.health_insurance)
