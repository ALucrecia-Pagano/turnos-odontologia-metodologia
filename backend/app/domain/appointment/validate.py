"""Validacion de un turno nuevo contra la agenda existente."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.domain.model import (
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    NewAppointmentRequest,
    ScheduleContext,
)
from app.domain.rules.duration import check_duration
from app.domain.rules.overlap import check_chair_overlap, check_professional_overlap
from app.domain.rules.references import check_references
from app.domain.rules.same_day import check_same_local_day
from app.domain.rules.start_time import check_start_time
from app.domain.violations import Ok, Rejected, ValidationResult, Violation


def _check_reference_ids(request: NewAppointmentRequest, references: AppointmentReferences) -> None:
    """Verifica que cada entidad recibida sea la que nombra el pedido.

    Raises:
        ValueError: Si alguna entidad no es `None` y su id no coincide con el del pedido
            (error de programacion del llamador, no una regla de negocio).
    """
    pairs = (
        ("patient", references.patient, request.patient_id),
        ("professional", references.professional, request.professional_id),
        ("chair", references.chair, request.chair_id),
        ("service", references.service, request.service_id),
    )
    for field, entity, expected_id in pairs:
        if entity is not None and entity.id != expected_id:
            raise ValueError(
                f"references.{field}.id ({entity.id}) no coincide con el id del pedido ({expected_id})"
            )


def _request_validity_violations(
    request: NewAppointmentRequest,
    references: AppointmentReferences,
    context: ScheduleContext,
    duration: int | None,
    end_at: datetime | None,
) -> list[Violation]:
    """Grupo 1, validez del pedido: referencias, duracion, inicio y medianoche (RN-AG-12).

    El orden es referencias -> duracion -> inicio en la grilla -> medianoche. La duracion
    efectiva es la explicita o, si no hay, la por defecto de la prestacion (aunque este
    inactiva). Si no hay ninguna de las dos (prestacion inexistente y sin duracion
    explicita) no hay nada que validar: el error util ya es `UNKNOWN_REFERENCE`. El inicio
    se evalua siempre; la medianoche solo si hay duracion efectiva sin violaciones.

    Args:
        request: Pedido de turno nuevo.
        references: Referencias resueltas por el llamador.
        context: Contexto de la agenda (zona horaria para la grilla y la medianoche).
        duration: Duracion efectiva en minutos, o `None` si no hay.
        end_at: Fin del turno calculado una sola vez (`None` si no hay duracion).

    C-05 a C-07 suman sus reglas al grupo que corresponda.
    """
    violations = check_references(request, references)
    duration_violations: list[Violation] = []
    if duration is not None:
        duration_violations = check_duration(duration)
        violations += duration_violations
    violations += check_start_time(request.start_at, context.tz)
    if end_at is not None and not duration_violations:
        violations += check_same_local_day(request.start_at, end_at, context.tz)
    return violations


def _effective_duration(
    request: NewAppointmentRequest, references: AppointmentReferences
) -> int | None:
    if request.duration_min is not None:
        return request.duration_min
    if references.service is not None:
        return references.service.default_duration_min
    return None


def _agenda_conflict_violations(
    candidate: Appointment, existing_appointments: Sequence[Appointment]
) -> list[Violation]:
    """Grupo 2, conflictos de agenda: profesional y despues sillon (RN-AG-12).

    C-05 a C-07 suman aca horario laboral, bloqueos y pasado, o en el grupo 1 si son
    reglas de validez del pedido.
    """
    return check_professional_overlap(candidate, existing_appointments) + check_chair_overlap(
        candidate, existing_appointments
    )


def validate_new_appointment(
    request: NewAppointmentRequest,
    references: AppointmentReferences,
    existing_appointments: Sequence[Appointment],
    context: ScheduleContext,
) -> ValidationResult:
    """Valida un turno nuevo y devuelve el turno aceptado o las violaciones.

    Evalua en dos grupos. Grupo 1, validez del pedido (referencias, duracion, inicio en la
    grilla y medianoche local, todas juntas y en ese orden): si hay alguna se devuelve
    `Rejected` sin evaluar el grupo 2. Grupo 2, conflictos de agenda (solapamientos por
    profesional y por sillon). Un resultado nunca mezcla violaciones de los dos grupos.

    Args:
        request: Pedido de turno nuevo.
        references: Referencias resueltas por el llamador (entidad o `None`); la
            prestacion aporta la duracion por defecto.
        existing_appointments: Turnos existentes de la agenda.
        context: Contexto de la agenda (zona horaria). Sin valor por defecto: el
            llamador debe pasarlo (SU-01). La grilla del inicio y la medianoche se evaluan
            en `context.tz`.

    Returns:
        `Ok` con el turno en estado `reservado`, o `Rejected` con las violaciones.

    Raises:
        ValueError: Si el id de alguna referencia no coincide con el del pedido.
    """
    _check_reference_ids(request, references)
    duration = _effective_duration(request, references)
    end_at = None if duration is None else request.start_at + timedelta(minutes=duration)
    validity_violations = _request_validity_violations(
        request, references, context, duration, end_at
    )
    # Sin duracion efectiva siempre hay UNKNOWN_REFERENCE (prestacion), asi que
    # `validity_violations` no esta vacia; la condicion `end_at is None` solo acota el tipo.
    if validity_violations or end_at is None:
        return Rejected(tuple(validity_violations))
    candidate = Appointment(
        id=request.id,
        patient_id=request.patient_id,
        professional_id=request.professional_id,
        chair_id=request.chair_id,
        service_id=request.service_id,
        start_at=request.start_at,
        end_at=end_at,
        status=AppointmentStatus.RESERVED,
    )
    conflict_violations = _agenda_conflict_violations(candidate, existing_appointments)
    if conflict_violations:
        return Rejected(tuple(conflict_violations))
    return Ok(candidate)
