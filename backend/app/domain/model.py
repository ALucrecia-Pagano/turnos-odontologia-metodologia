"""Modelo del dominio de la agenda: estados, turnos y pedido de turno nuevo.

Todos los ids son `uuid.UUID` y los inyecta el llamador (la capa de aplicacion).
El dominio usa `UUID` solo como tipo y nunca llama a `uuid4()` ni genera ids, igual
que `now` se inyecta: asi el resultado es determinista y los tests comparan contra
valores literales.

Todo instante (`datetime`) debe tener zona horaria y se normaliza a UTC al construir
el valor. Un instante sin zona es un error de programacion del llamador y se rechaza
con `ValueError`, no con una violacion de negocio.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from app.domain.intervals import Interval


class AppointmentStatus(Enum):
    """Estado de un turno. Los valores son los estados en espanol de la base de datos."""

    RESERVED = "reservado"
    CONFIRMED = "confirmado"
    ATTENDED = "atendido"
    NO_SHOW = "ausente"
    CANCELLED = "cancelado"


def _to_utc(field_name: str, value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} necesita zona horaria (datetime naive)")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Service:
    """Prestacion del catalogo, con su duracion por defecto.

    Attributes:
        id: Identificador de la prestacion.
        default_duration_min: Duracion por defecto en minutos. No se valida aca: la
            duracion efectiva se valida en `rules/duration.py`.
    """

    id: UUID
    default_duration_min: int


@dataclass(frozen=True, slots=True)
class NewAppointmentRequest:
    """Pedido de un turno nuevo.

    No lleva `service_id`: la prestacion llega como argumento aparte al validar.

    Attributes:
        id: Id del turno nuevo, generado por el llamador.
        patient_id: Paciente.
        professional_id: Profesional.
        chair_id: Sillon.
        start_at: Inicio del turno (con zona horaria; se normaliza a UTC).
        duration_min: Duracion explicita en minutos, o `None` para usar la de la prestacion.

    Raises:
        ValueError: Si `start_at` no tiene zona horaria.
    """

    id: UUID
    patient_id: UUID
    professional_id: UUID
    chair_id: UUID
    start_at: datetime
    duration_min: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))


@dataclass(frozen=True, slots=True)
class Appointment:
    """Turno de la agenda. Ocupa el intervalo semiabierto `[start_at, end_at)`.

    Attributes:
        id: Id del turno.
        patient_id: Paciente.
        professional_id: Profesional.
        chair_id: Sillon.
        service_id: Prestacion.
        start_at: Inicio (UTC).
        end_at: Fin (UTC).
        status: Estado del turno.

    Raises:
        ValueError: Si algun instante no tiene zona horaria o si `start_at >= end_at`.
    """

    id: UUID
    patient_id: UUID
    professional_id: UUID
    chair_id: UUID
    service_id: UUID
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))
        object.__setattr__(self, "end_at", _to_utc("end_at", self.end_at))
        if self.start_at >= self.end_at:
            raise ValueError("start_at debe ser anterior a end_at")

    @property
    def interval(self) -> Interval:
        """Intervalo semiabierto `[start_at, end_at)` que ocupa el turno."""
        return Interval(self.start_at, self.end_at)
