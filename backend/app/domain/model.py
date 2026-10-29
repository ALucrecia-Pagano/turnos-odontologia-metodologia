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
class WorkingHours:
    """Tramo del horario de atencion de un profesional en un dia de la semana (RN-DI-01).

    El tramo es el intervalo semiabierto `[start_minute, end_minute)` en minutos locales
    desde las 00:00 (KB 04): 540 es las 09:00 y 1440 es las 24:00. No valida nada al
    construirse: los tramos los carga el usuario y su validez la decide
    `validate_working_hours`, que devuelve violaciones y no lanza excepciones.

    Attributes:
        professional_id: Profesional al que pertenece el tramo.
        weekday: Dia de la semana ISO: 1 = lunes ... 7 = domingo.
        start_minute: Minuto local de inicio, desde las 00:00.
        end_minute: Minuto local de fin, desde las 00:00 (1440 = 24:00).
    """

    professional_id: UUID
    weekday: int
    start_minute: int
    end_minute: int


@dataclass(frozen=True, slots=True)
class Block:
    """Bloqueo de la agenda de un profesional: vacaciones, feriado o ausencia (RN-DI-03).

    Ocupa el intervalo semiabierto `[start_at, end_at)` de instantes, que puede durar
    varios dias (KB 04). Al construirse solo normaliza los instantes a UTC: el orden
    `start_at < end_at` lo carga el usuario y lo decide `validate_block`, que devuelve
    violaciones y no lanza excepciones.

    Attributes:
        id: Id del bloqueo.
        professional_id: Profesional bloqueado.
        start_at: Inicio (con zona horaria; se normaliza a UTC).
        end_at: Fin (con zona horaria; se normaliza a UTC).
        reason: Motivo opcional (por ejemplo, "vacaciones").

    Raises:
        ValueError: Si algun instante no tiene zona horaria (error de programacion).
    """

    id: UUID
    professional_id: UUID
    start_at: datetime
    end_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))
        object.__setattr__(self, "end_at", _to_utc("end_at", self.end_at))


@dataclass(frozen=True, slots=True)
class ScheduleContext:
    """Contexto de la agenda que recibe el dominio junto con el pedido.

    La zona se recibe por parametro: el dominio no la lee del entorno ni la fija (SU-01).
    El borde (API) convierte `APP_TIMEZONE` en `ZoneInfo`. C-07 suma aca `now` sin volver
    a cambiar la firma.

    Attributes:
        tz: Zona horaria en la que se evaluan la grilla del inicio, la medianoche y el
            horario de atencion, y en la que se muestran las horas de los mensajes.
        working_hours: Tramos del horario de atencion. Sin valor por defecto: un llamador
            que no los pase falla en mypy. El dominio elige los del profesional del pedido
            y del dia de la semana local; el llamador no necesita filtrarlos.
        blocks: Bloqueos de la agenda. Sin valor por defecto, por la misma razon. El
            dominio elige los del profesional del pedido; el llamador no necesita
            filtrarlos. Se suponen validos (`validate_block`): no se revalidan.
    """

    tz: ZoneInfo
    working_hours: tuple[WorkingHours, ...]
    blocks: tuple[Block, ...]


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
