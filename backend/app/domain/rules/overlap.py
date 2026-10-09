"""Reglas de solapamiento de agenda por profesional y por sillon (RN-AG-01, RN-AG-02)."""

from collections.abc import Callable, Sequence

from app.domain.intervals import overlaps
from app.domain.model import Appointment, AppointmentStatus
from app.domain.violations import Violation, ViolationCode

OCCUPYING_STATUSES: frozenset[AppointmentStatus] = frozenset(
    {AppointmentStatus.RESERVED, AppointmentStatus.CONFIRMED, AppointmentStatus.ATTENDED}
)


def _conflicting(
    candidate: Appointment,
    existing: Sequence[Appointment],
    same_resource: Callable[[Appointment], bool],
) -> list[Appointment]:
    """Turnos existentes que ocupan agenda, comparten recurso y se solapan, en orden estable.

    El orden es `(start_at, str(id))`: el id solo desempata dos turnos con el mismo
    inicio, para que el resultado no dependa del orden de la lista recibida.
    """
    return sorted(
        (
            other
            for other in existing
            if other.status in OCCUPYING_STATUSES
            and same_resource(other)
            and overlaps(candidate.interval, other.interval)
        ),
        key=lambda other: (other.start_at, str(other.id)),
    )


def check_professional_overlap(
    candidate: Appointment, existing: Sequence[Appointment]
) -> list[Violation]:
    """Una violacion `PROFESSIONAL_OVERLAP` por cada turno del mismo profesional que se solapa.

    Args:
        candidate: Turno que se quiere dar.
        existing: Turnos existentes, sin filtrar.

    Returns:
        Violaciones ordenadas por inicio del turno en conflicto; vacia si no hay choque.
    """
    return [
        Violation(
            code=ViolationCode.PROFESSIONAL_OVERLAP,
            message=f"El profesional ya tiene un turno que se superpone (turno {other.id}).",
            conflicting_appointment_id=other.id,
        )
        for other in _conflicting(
            candidate, existing, lambda other: other.professional_id == candidate.professional_id
        )
    ]


def check_chair_overlap(candidate: Appointment, existing: Sequence[Appointment]) -> list[Violation]:
    """Una violacion `CHAIR_OVERLAP` por cada turno del mismo sillon que se solapa.

    Args:
        candidate: Turno que se quiere dar.
        existing: Turnos existentes, sin filtrar.

    Returns:
        Violaciones ordenadas por inicio del turno en conflicto; vacia si no hay choque.
    """
    return [
        Violation(
            code=ViolationCode.CHAIR_OVERLAP,
            message=f"El sillón ya está ocupado por un turno que se superpone (turno {other.id}).",
            conflicting_appointment_id=other.id,
        )
        for other in _conflicting(
            candidate, existing, lambda other: other.chair_id == candidate.chair_id
        )
    ]
