"""Validacion de un turno nuevo contra la agenda existente."""

from collections.abc import Sequence
from datetime import timedelta

from app.domain.model import Appointment, AppointmentStatus, NewAppointmentRequest, Service
from app.domain.rules.duration import check_positive_duration
from app.domain.rules.overlap import check_chair_overlap, check_professional_overlap
from app.domain.violations import Ok, Rejected, ValidationResult


def validate_new_appointment(
    request: NewAppointmentRequest,
    service: Service,
    existing_appointments: Sequence[Appointment],
) -> ValidationResult:
    """Valida un turno nuevo y devuelve el turno aceptado o las violaciones.

    Args:
        request: Pedido de turno nuevo.
        service: Prestacion pedida; aporta el id y la duracion por defecto.
        existing_appointments: Turnos existentes de la agenda.

    Returns:
        `Ok` con el turno en estado `reservado`, o `Rejected` con las violaciones.
    """
    duration = (
        request.duration_min if request.duration_min is not None else service.default_duration_min
    )
    duration_violations = check_positive_duration(duration)
    if duration_violations:
        return Rejected(tuple(duration_violations))
    candidate = Appointment(
        id=request.id,
        patient_id=request.patient_id,
        professional_id=request.professional_id,
        chair_id=request.chair_id,
        service_id=service.id,
        start_at=request.start_at,
        end_at=request.start_at + timedelta(minutes=duration),
        status=AppointmentStatus.RESERVED,
    )
    violations = check_professional_overlap(candidate, existing_appointments) + check_chair_overlap(
        candidate, existing_appointments
    )
    if violations:
        return Rejected(tuple(violations))
    return Ok(candidate)
