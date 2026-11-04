"""Modelo del dominio de la agenda: estados, turnos y pedido de turno nuevo.

Todos los ids son `uuid.UUID` y los inyecta el llamador (la capa de aplicacion).
El dominio usa `UUID` solo como tipo y nunca llama a `uuid4()` ni genera ids, igual
que `now` se inyecta: asi el resultado es determinista y los tests comparan contra
valores literales.

Todo instante (`datetime`) debe tener zona horaria y se normaliza a UTC al construir
el valor. Un instante sin zona es un error de programacion del llamador y se rechaza
con `ValueError`, no con una violacion de negocio.
"""

from dataclasses import dataclass, field
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


class Role(Enum):
    """Rol autenticado por el borde; el dominio solo aplica permisos."""

    ODONTOLOGO = "odontologo"
    RECEPCION = "recepcion"
    ADMINISTRADOR = "administrador"


@dataclass(frozen=True, slots=True)
class Actor:
    """Identidad del usuario y vínculo profesional explícito, recibidos del borde."""

    user_id: UUID
    role: Role
    professional_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.role is Role.ODONTOLOGO and self.professional_id is None:
            raise ValueError("El actor odontólogo necesita professional_id")


def _to_utc(field_name: str, value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} necesita zona horaria (datetime naive)")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Professional:
    """Profesional de la agenda (modelo minimo: solo lo que usan las reglas).

    Attributes:
        id: Identificador del profesional.
        full_name: Nombre completo. Obligatorio y sin valor por defecto; no se valida ni se
            recorta al construir (la validez del nombre es del alta del catalogo). Lo usan los
            mensajes de los conflictos de agenda, que lo muestran recortado.
        active: `True` si el profesional esta activo.
    """

    id: UUID
    full_name: str
    active: bool


@dataclass(frozen=True, slots=True)
class Chair:
    """Sillon del consultorio (modelo minimo: solo lo que usan las reglas).

    Attributes:
        id: Identificador del sillon.
        name: Nombre del sillon. Obligatorio y sin valor por defecto; no se valida ni se
            recorta al construir (la validez del nombre es del alta del catalogo). Lo usan los
            mensajes de los conflictos de agenda, que lo muestran recortado.
        active: `True` si el sillon esta activo.
    """

    id: UUID
    name: str
    active: bool


@dataclass(frozen=True, slots=True)
class Patient:
    """Paciente mínimo sin clínica: nombre/DNI se validan en el alta, no al construir.

    Attributes:
        id: Identificador del paciente.
        full_name: Nombre original sin validar.
        dni: DNI recibido; el alta lo normaliza.
        phone: Texto libre opcional.
        health_insurance: Obra social como texto libre opcional.
    """

    id: UUID
    full_name: str
    dni: str
    phone: str | None = None
    health_insurance: str | None = None


@dataclass(frozen=True, slots=True)
class Service:
    """Prestacion del catalogo, con su duracion por defecto.

    Attributes:
        id: Identificador de la prestacion.
        name: Nombre original; la validez y unicidad se evalúan en el alta.
        default_duration_min: Duracion por defecto en minutos. No se valida aca: la
            duracion efectiva se valida en `rules/duration.py`.
        active: `True` si la prestacion esta activa.
    """

    id: UUID
    name: str
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
        changed_by: Id del usuario (`Actor.user_id`) que solicita el alta del turno.

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
    changed_by: UUID = field(kw_only=True)

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_at", _to_utc("start_at", self.start_at))


@dataclass(frozen=True, slots=True)
class RescheduleRequest:
    """Pedido de reprogramacion de un turno existente (RN-TU-03, US-031).

    Solo el inicio es obligatorio. El profesional, el sillon y la duracion son
    opcionales: `None` significa "conservar el valor actual del turno". El
    paciente y la prestacion no se cambian en una reprogramacion (se toman del
    turno original), asi que no aparecen aca.

    Attributes:
        start_at: Nuevo inicio del turno (con zona horaria; se normaliza a UTC).
        professional_id: Profesional del nuevo destino, o `None` para conservar
            el profesional actual del turno.
        chair_id: Sillon del nuevo destino, o `None` para conservar el sillon
            actual del turno.
        duration_min: Nueva duracion explicita en minutos, o `None` para
            conservar la duracion real actual del turno (fin menos inicio).

    Raises:
        ValueError: Si `start_at` no tiene zona horaria.
    """

    start_at: datetime
    professional_id: UUID | None = None
    chair_id: UUID | None = None
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
    El borde (API) convierte `APP_TIMEZONE` en `ZoneInfo`. El momento actual (`now`) tambien
    se inyecta: el dominio no lee el reloj (RN-GL-04).

    Attributes:
        tz: Zona horaria en la que se evaluan la grilla del inicio, la medianoche y el
            horario de atencion, y en la que se muestran las horas de los mensajes.
        working_hours: Tramos del horario de atencion. Sin valor por defecto: un llamador
            que no los pase falla en mypy. El dominio elige los del profesional del pedido
            y del dia de la semana local; el llamador no necesita filtrarlos.
        blocks: Bloqueos de la agenda. Sin valor por defecto, por la misma razon. El
            dominio elige los del profesional del pedido; el llamador no necesita
            filtrarlos. Se suponen validos (`validate_block`): no se revalidan.
        now: Instante actual, inyectado por el llamador (RN-GL-04); el dominio nunca lee
            el reloj. Sin valor por defecto, por la misma razon. Se normaliza a UTC al
            construir el contexto. Lo usa la regla del pasado (RN-AG-06).

    Raises:
        ValueError: Si `now` no tiene zona horaria (error de programacion).
    """

    tz: ZoneInfo
    working_hours: tuple[WorkingHours, ...]
    blocks: tuple[Block, ...]
    now: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "now", _to_utc("now", self.now))


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


@dataclass(frozen=True, slots=True)
class RescheduleDetail:
    """Detalle tipado de una reprogramacion registrada en el historial (US-031 CA-5, US-033).

    Attributes:
        previous_interval: Intervalo en UTC del turno antes de reprogramar.
        new_interval: Intervalo en UTC del turno reprogramado.
        previous_professional_id: Profesional anterior.
        new_professional_id: Profesional nuevo.
        previous_chair_id: Sillon anterior.
        new_chair_id: Sillon nuevo.
    """

    previous_interval: Interval
    new_interval: Interval
    previous_professional_id: UUID
    new_professional_id: UUID
    previous_chair_id: UUID
    new_chair_id: UUID


@dataclass(frozen=True, slots=True)
class AppointmentStatusChange:
    """Entrada inmutable del historial funcional de transiciones de estado (RN-TU-06, US-033).

    Attributes:
        appointment_id: Id del turno al que pertenece la transicion.
        from_status: Estado previo del turno, o `None` unicamente en el alta inicial.
        to_status: Nuevo estado del turno tras la operacion.
        changed_by: Id del usuario (`Actor.user_id`) que realizo la operacion.
        changed_at: Instante del cambio (con zona horaria; se normaliza a UTC).
        reschedule: Detalle de reprogramacion cuando la entrada proviene de
            `reschedule_appointment`, o `None` en el alta, cambio de estado y cancelacion.
    """

    appointment_id: UUID
    from_status: AppointmentStatus | None
    to_status: AppointmentStatus
    changed_by: UUID
    changed_at: datetime
    reschedule: RescheduleDetail | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "changed_at", _to_utc("changed_at", self.changed_at))
        if self.from_status == self.to_status and self.reschedule is None:
            raise ValueError(
                "AppointmentStatusChange con el mismo from_status y to_status requiere reschedule"
            )
