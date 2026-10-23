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
from zoneinfo import ZoneInfo

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
class Professional:
    """Profesional de la agenda (modelo minimo: solo lo que usan las reglas).

    Attributes:
        id: Identificador del profesional.
        active: `True` si el profesional esta activo.
    """

    id: UUID
    active: bool


@dataclass(frozen=True, slots=True)
class Chair:
    """Sillon del consultorio (modelo minimo: solo lo que usan las reglas).

    Attributes:
        id: Identificador del sillon.
        active: `True` si el sillon esta activo.
    """

    id: UUID
    active: bool


@dataclass(frozen=True, slots=True)
class Patient:
    """Paciente (modelo minimo: las reglas solo piden que exista).

    Attributes:
        id: Identificador del paciente.
    """

    id: UUID


@dataclass(frozen=True, slots=True)
class Service:
    """Prestacion del catalogo, con su duracion por defecto.

    Attributes:
        id: Identificador de la prestacion.
        default_duration_min: Duracion por defecto en minutos. No se valida aca: la
            duracion efectiva se valida en `rules/duration.py`.
        active: `True` si la prestacion esta activa.
    """

    id: UUID
    default_duration_min: int
    active: bool = True


@dataclass(frozen=True, slots=True)
class NewAppointmentRequest:
    """Pedido de un turno nuevo.

    Attributes:
        id: Id del turno nuevo, generado por el llamador.
        patient_id: Paciente.
        professional_id: Profesional.
        chair_id: Sillon.
        service_id: Prestacion pedida.
        start_at: Inicio del turno (con zona horaria; se normaliza a UTC).
        duration_min: Duracion explicita en minutos, o `None` para usar la de la prestacion.

    Raises:
        ValueError: Si `start_at` no tiene zona horaria.
    """

    id: UUID
    patient_id: UUID
    professional_id: UUID
    chair_id: UUID
    service_id: UUID
    start_at: datetime
    duration_min: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))


@dataclass(frozen=True, slots=True)
class AppointmentReferences:
    """Referencias del pedido que resolvio el llamador: la entidad o `None` si no existe.

    Attributes:
        patient: Paciente, o `None` si no existe.
        professional: Profesional, o `None` si no existe.
        chair: Sillon, o `None` si no existe.
        service: Prestacion, o `None` si no existe.
    """

    patient: Patient | None
    professional: Professional | None
    chair: Chair | None
    service: Service | None


@dataclass(frozen=True, slots=True)
class ScheduleContext:
    """Contexto de la agenda que recibe el dominio junto con el pedido.

    La zona se recibe por parametro: el dominio no la lee del entorno ni la fija (SU-01).
    El borde (API) convierte `APP_TIMEZONE` en `ZoneInfo`. Los proximos changes suman
    aca horarios, bloqueos y `now` sin volver a cambiar la firma.

    Attributes:
        tz: Zona horaria en la que se evaluan la grilla del inicio y la medianoche.
    """

    tz: ZoneInfo


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
