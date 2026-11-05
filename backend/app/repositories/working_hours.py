from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import ProfessionalModel, WorkingHoursModel
from app.domain.catalog.result import CatalogResult, Ok
from app.domain.model import WorkingHours
from app.domain.rules.working_hours import validate_working_hours
from app.domain.violations import ReferenceKind, Rejected, Violation, ViolationCode


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


def _unknown_reference(professional_id: UUID) -> Rejected:
    return Rejected(
        (
            Violation(
                code=ViolationCode.UNKNOWN_REFERENCE,
                message=f"El profesional indicado no existe (id {professional_id}).",
                reference_kind=ReferenceKind.PROFESSIONAL,
            ),
        )
    )


class WorkingHoursRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_professional(
        self, professional_id: UUID, slots: Sequence[WorkingHours]
    ) -> CatalogResult[tuple[WorkingHours, ...]]:
        candidate_slots = tuple(slots)
        if any(slot.professional_id != professional_id for slot in candidate_slots):
            raise ValueError("Todos los tramos deben pertenecer al profesional indicado.")
        violations = validate_working_hours(candidate_slots)
        if violations:
            return Rejected(tuple(violations))
        if not candidate_slots and self._session.get(ProfessionalModel, professional_id) is None:
            return _unknown_reference(professional_id)
        try:
            with self._session.begin_nested():
                self._session.execute(
                    delete(WorkingHoursModel).where(
                        WorkingHoursModel.professional_id == professional_id
                    )
                )
                for slot in candidate_slots:
                    self._session.add(
                        WorkingHoursModel(
                            id=uuid4(),
                            professional_id=slot.professional_id,
                            weekday=slot.weekday,
                            start_minute=slot.start_minute,
                            end_minute=slot.end_minute,
                        )
                    )
                self._session.flush()
        except IntegrityError as error:
            if _constraint_name(error) == "fk_working_hours_professional_id_professional":
                return _unknown_reference(professional_id)
            raise
        ordered = tuple(sorted(candidate_slots, key=lambda slot: (slot.weekday, slot.start_minute)))
        return Ok(ordered)

    def list_by_professional(self, professional_id: UUID) -> tuple[WorkingHours, ...]:
        rows = self._session.scalars(
            select(WorkingHoursModel)
            .where(WorkingHoursModel.professional_id == professional_id)
            .order_by(WorkingHoursModel.weekday, WorkingHoursModel.start_minute)
        ).all()
        return tuple(self._to_domain(row) for row in rows)

    def list(self) -> tuple[WorkingHours, ...]:
        rows = self._session.scalars(
            select(WorkingHoursModel).order_by(
                WorkingHoursModel.professional_id,
                WorkingHoursModel.weekday,
                WorkingHoursModel.start_minute,
            )
        ).all()
        return tuple(self._to_domain(row) for row in rows)

    @staticmethod
    def _to_domain(row: WorkingHoursModel) -> WorkingHours:
        return WorkingHours(row.professional_id, row.weekday, row.start_minute, row.end_minute)
