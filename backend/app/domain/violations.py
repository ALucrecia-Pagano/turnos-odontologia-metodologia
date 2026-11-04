"""Resultado tipado de la validacion: `Ok` con el turno o `Rejected` con violaciones.

Las reglas de negocio nunca se informan con excepciones: se devuelven como
`Violation` con un codigo estable (el que expone la API) y un mensaje en espanol.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias
from uuid import UUID

from app.domain.intervals import Interval
from app.domain.model import Appointment, AppointmentStatusChange


class ViolationCode(Enum):
    """Codigo estable de una violacion. El valor es igual al nombre."""

    PROFESSIONAL_OVERLAP = "PROFESSIONAL_OVERLAP"
    CHAIR_OVERLAP = "CHAIR_OVERLAP"
    INVALID_DURATION = "INVALID_DURATION"
    UNKNOWN_REFERENCE = "UNKNOWN_REFERENCE"
    INACTIVE_REFERENCE = "INACTIVE_REFERENCE"
    CROSSES_MIDNIGHT = "CROSSES_MIDNIGHT"
    INVALID_START_TIME = "INVALID_START_TIME"
    OUTSIDE_WORKING_HOURS = "OUTSIDE_WORKING_HOURS"
    INVALID_WORKING_HOURS = "INVALID_WORKING_HOURS"
    OVERLAPPING_WORKING_HOURS = "OVERLAPPING_WORKING_HOURS"
    BLOCKED_TIME = "BLOCKED_TIME"
    INVALID_BLOCK = "INVALID_BLOCK"
    IN_THE_PAST = "IN_THE_PAST"
    DUPLICATE_DNI = "DUPLICATE_DNI"
    INVALID_DNI = "INVALID_DNI"
    DUPLICATE_NAME = "DUPLICATE_NAME"
    EMPTY_NAME = "EMPTY_NAME"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    FORBIDDEN_OPERATION = "FORBIDDEN_OPERATION"
    STATUS_CHANGE_TOO_EARLY = "STATUS_CHANGE_TOO_EARLY"


class ReferenceKind(Enum):
    """Tipo de referencia que fallo (paciente, profesional, sillon o prestacion).

    El valor es igual al nombre. Lo usa el frontend para marcar el campo del formulario.
    """

    PATIENT = "PATIENT"
    PROFESSIONAL = "PROFESSIONAL"
    CHAIR = "CHAIR"
    SERVICE = "SERVICE"


@dataclass(frozen=True, slots=True)
class Violation:
    """Una regla de negocio incumplida.

    Attributes:
        code: Codigo estable.
        message: Mensaje en espanol.
        conflicting_appointment_id: Id del turno en conflicto, si corresponde.
        reference_kind: Tipo de referencia que fallo, solo en las violaciones de
            referencias (`UNKNOWN_REFERENCE` / `INACTIVE_REFERENCE`); `None` en el resto.
        conflicting_block_id: Id del bloqueo en conflicto, solo en `BLOCKED_TIME`; `None`
            en el resto.
        conflicting_interval: Intervalo en UTC del turno o del bloqueo en conflicto, solo
            en `PROFESSIONAL_OVERLAP`, `CHAIR_OVERLAP` y `BLOCKED_TIME`; `None` en el resto
            (tambien en `OUTSIDE_WORKING_HOURS`). Invariante: hay intervalo si y solo si hay
            `conflicting_appointment_id` o `conflicting_block_id`. En un bloqueo es el
            intervalo completo, aunque dure varios dias. Los dos ultimos campos van al final
            para no cambiar las construcciones existentes.
    """

    code: ViolationCode
    message: str
    conflicting_appointment_id: UUID | None = None
    reference_kind: ReferenceKind | None = None
    conflicting_block_id: UUID | None = None
    conflicting_interval: Interval | None = None


@dataclass(frozen=True, slots=True)
class Ok:
    """Turno aceptado.

    Attributes:
        appointment: Turno aceptado por alta o transición, con su estado resultante.
        status_change: Entrada inmutable de historial generada por la operación aceptada.
    """

    appointment: Appointment
    status_change: AppointmentStatusChange


@dataclass(frozen=True, slots=True)
class Rejected:
    """Turno rechazado.

    Attributes:
        violations: Todas las violaciones, en orden estable. No puede estar vacia.

    Raises:
        ValueError: Si `violations` esta vacia.
    """

    violations: tuple[Violation, ...]

    def __post_init__(self) -> None:
        if not self.violations:
            raise ValueError("Rejected necesita al menos una violacion")


ValidationResult: TypeAlias = Ok | Rejected
