"""Reglas de solapamiento de agenda por profesional y por sillon (RN-AG-01, RN-AG-02)."""

from collections.abc import Callable, Sequence
from typing import Final
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_time, overlaps
from app.domain.model import Appointment, AppointmentStatus
from app.domain.rules.names import subject_name
from app.domain.violations import Violation, ViolationCode

_GENERIC_PROFESSIONAL: Final = "El profesional"
_GENERIC_CHAIR: Final = "El sillón"

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
    candidate: Appointment, existing: Sequence[Appointment], tz: ZoneInfo, professional_name: str
) -> list[Violation]:
    """Una violacion `PROFESSIONAL_OVERLAP` por cada turno del mismo profesional que se solapa.

    Args:
        candidate: Turno que se quiere dar.
        existing: Turnos existentes, sin filtrar.
        tz: Zona horaria para mostrar el rango del turno existente.
        professional_name: Nombre del profesional; vacio o en blanco usa el generico.

    Returns:
        Violaciones ordenadas por inicio del turno en conflicto, cada una con su id y su
        `conflicting_interval` (el del turno existente, en UTC); vacia si no hay choque.
    """
    subject = subject_name(professional_name, _GENERIC_PROFESSIONAL)
    return [
        Violation(
            code=ViolationCode.PROFESSIONAL_OVERLAP,
            message=(
                f"{subject} ya tiene un turno de {format_local_time(other.start_at, tz)} "
                f"a {format_local_time(other.end_at, tz)} (hora local) que se superpone "
                f"(turno {other.id})."
            ),
            conflicting_appointment_id=other.id,
            conflicting_interval=other.interval,
        )
        for other in _conflicting(
            candidate, existing, lambda other: other.professional_id == candidate.professional_id
        )
    ]


def check_chair_overlap(
    candidate: Appointment, existing: Sequence[Appointment], tz: ZoneInfo, chair_name: str
) -> list[Violation]:
    """Una violacion `CHAIR_OVERLAP` por cada turno del mismo sillon que se solapa.

    Args:
        candidate: Turno que se quiere dar.
        existing: Turnos existentes, sin filtrar.
        tz: Zona horaria para mostrar el rango del turno existente.
        chair_name: Nombre del sillon; vacio o en blanco usa el generico.

    Returns:
        Violaciones ordenadas por inicio del turno en conflicto, cada una con su id y su
        `conflicting_interval` (el del turno existente, en UTC); vacia si no hay choque.
    """
    subject = subject_name(chair_name, _GENERIC_CHAIR)
    return [
        Violation(
            code=ViolationCode.CHAIR_OVERLAP,
            message=(
                f"{subject} está ocupado de {format_local_time(other.start_at, tz)} "
                f"a {format_local_time(other.end_at, tz)} (hora local) por un turno que se "
                f"superpone (turno {other.id})."
            ),
            conflicting_appointment_id=other.id,
            conflicting_interval=other.interval,
        )
        for other in _conflicting(
            candidate, existing, lambda other: other.chair_id == candidate.chair_id
        )
    ]
