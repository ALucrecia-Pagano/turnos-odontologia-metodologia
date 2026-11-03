"""Operacion pura de reprogramar un turno existente (RN-TU-03, US-031).

Reprogramar revalida todas las reglas RN-AG del turno nuevo reutilizando
`validate_new_appointment`, excluyendo al propio turno de los existentes por id.
Solo se acepta desde `reservado` o `confirmado`; el turno aceptado vuelve a
`reservado` y conserva su id. El odontologo no reprograma; recepcion y
administrador reprograman todos. El orden de evaluacion es permiso (corta),
estado (corta) y turno nuevo. El verbo del mensaje de `IN_THE_PAST` llega a la
regla del pasado a traves de `validate_new_appointment`, que recibe `operation`
(default "dar turnos"); reprogramar pasa "reprogramar turnos". Sin I/O ni reloj
global: `now` vive en `context`.
"""

from collections.abc import Sequence
from datetime import datetime

from app.domain.appointment.validate import validate_new_appointment
from app.domain.intervals import format_local_date_time, format_local_time
from app.domain.model import (
    Actor,
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    NewAppointmentRequest,
    RescheduleRequest,
    Role,
    ScheduleContext,
)
from app.domain.rules.names import subject_name
from app.domain.violations import Rejected, ValidationResult, Violation, ViolationCode

_RESCHEDULABLE: frozenset[AppointmentStatus] = frozenset(
    {AppointmentStatus.RESERVED, AppointmentStatus.CONFIRMED}
)
_REPROGRAMAR_OPERATION = "reprogramar turnos"


def reschedule_appointment(
    appointment: Appointment,
    request: RescheduleRequest,
    references: AppointmentReferences,
    existing_appointments: Sequence[Appointment],
    actor: Actor,
    professional_name: str,
    context: ScheduleContext,
) -> ValidationResult:
    """Reprograma un turno revalidando todas las RN-AG excluyendo al propio.

    El inicio del nuevo slot es obligatorio; el profesional, el sillon y la duracion
    del pedido son opcionales (`None` conserva el valor actual del turno). El paciente
    y la prestacion se toman del turno original: no se cambian. La duracion efectiva al
    omitirla es la duracion real actual del turno (fin menos inicio). El turno aceptado
    conserva su id y vuelve a `reservado`.

    Args:
        appointment: Turno a reprogramar (estado e intervalo actuales).
        request: Pedido de reprogramacion (nuevo inicio; pro/sillon/duracion opcionales).
        references: Referencias resueltas para el nuevo destino (profesional/sillon si
            cambiaron; paciente y prestacion del original, siempre revalidados).
        existing_appointments: Agenda completa, incluido el turno a reprogramar; el
            dominio lo excluye por id antes de revalidar.
        actor: Usuario que reprograma; el odontologo no puede.
        professional_name: Nombre del profesional ORIGINAL, para los mensajes de permiso
            y estado que describen el turno actual.
        context: Contexto de la agenda (zona, tramos, bloqueos y `now`, fuente unica del
            reloj).

    Returns:
        `Ok` con el turno reprogramado en `reservado` (mismo id), o `Rejected` con
        `FORBIDDEN_OPERATION` (permiso), `INVALID_TRANSITION` (estado terminal) o las
        violaciones del turno nuevo revalidado (orden RN-AG-12).
    """
    if actor.role is Role.ODONTOLOGO:
        return Rejected((_forbidden_operation(appointment, professional_name, context),))
    if appointment.status not in _RESCHEDULABLE:
        return Rejected((_invalid_transition(appointment, professional_name, context),))
    others = [other for other in existing_appointments if other.id != appointment.id]
    return validate_new_appointment(
        _build_request(appointment, request),
        references,
        others,
        context,
        operation=_REPROGRAMAR_OPERATION,
    )


def _build_request(appointment: Appointment, request: RescheduleRequest) -> NewAppointmentRequest:
    """Construye el pedido equivalente al alta, conservando lo que no se cambia.

    El id, el paciente y la prestacion salen del turno original; el profesional, el
    sillon y el inicio del pedido; la duracion, la del pedido o, si se omite, la
    duracion real actual del turno (fin menos inicio), no el default de la prestacion.
    """
    duration = request.duration_min
    if duration is None:
        duration = int((appointment.end_at - appointment.start_at).total_seconds() // 60)
    professional_id = request.professional_id
    if professional_id is None:
        professional_id = appointment.professional_id
    chair_id = request.chair_id
    if chair_id is None:
        chair_id = appointment.chair_id
    return NewAppointmentRequest(
        id=appointment.id,
        patient_id=appointment.patient_id,
        professional_id=professional_id,
        chair_id=chair_id,
        service_id=appointment.service_id,
        start_at=request.start_at,
        duration_min=duration,
    )


def _turn_description(
    appointment: Appointment, professional_name: str, context: ScheduleContext
) -> str:
    """Descripcion del turno ORIGINAL para los mensajes de permiso y estado.

    Reutiliza los formatos locales vigentes (fecha local e intervalo en hora local) y
    `subject_name` (recorta el nombre; vacio/blanco usa "el profesional").
    """
    name = subject_name(professional_name, "el profesional")
    day = format_local_date_time(appointment.start_at, context.tz).split(" ")[0]
    start = format_local_time(appointment.start_at, context.tz)
    end = format_local_time(appointment.end_at, context.tz)
    return f"turno de {name} del {day} de {start} a {end} (hora local)"


def _forbidden_operation(
    appointment: Appointment, professional_name: str, context: ScheduleContext
) -> Violation:
    return Violation(
        ViolationCode.FORBIDDEN_OPERATION,
        f"No tiene permiso para reprogramar el {_turn_description(appointment, professional_name, context)}: "
        "solo recepción y administración pueden reprogramar turnos.",
    )


def _invalid_transition(
    appointment: Appointment, professional_name: str, context: ScheduleContext
) -> Violation:
    return Violation(
        ViolationCode.INVALID_TRANSITION,
        f"El {_turn_description(appointment, professional_name, context)} no se puede "
        f'reprogramar porque está en estado terminal "{appointment.status.value}".',
    )
