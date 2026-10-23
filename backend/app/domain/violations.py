"""Resultado tipado de la validacion: `Ok` con el turno o `Rejected` con violaciones.

Las reglas de negocio nunca se informan con excepciones: se devuelven como
`Violation` con un codigo estable (el que expone la API) y un mensaje en espanol.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias
from uuid import UUID

from app.domain.model import Appointment


class ViolationCode(Enum):
    """Codigo estable de una violacion. El valor es igual al nombre."""

    PROFESSIONAL_OVERLAP = "PROFESSIONAL_OVERLAP"
    CHAIR_OVERLAP = "CHAIR_OVERLAP"
    INVALID_DURATION = "INVALID_DURATION"
    UNKNOWN_REFERENCE = "UNKNOWN_REFERENCE"
    INACTIVE_REFERENCE = "INACTIVE_REFERENCE"
    CROSSES_MIDNIGHT = "CROSSES_MIDNIGHT"
    INVALID_START_TIME = "INVALID_START_TIME"


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
    """

    code: ViolationCode
    message: str
    conflicting_appointment_id: UUID | None = None
    reference_kind: ReferenceKind | None = None


@dataclass(frozen=True, slots=True)
class Ok:
    """Turno aceptado.

    Attributes:
        appointment: El turno nuevo, en estado `reservado`.
    """

    appointment: Appointment


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
