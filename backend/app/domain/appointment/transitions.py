"""Política pura de transiciones ordinarias del turno."""

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.domain.intervals import (
    format_local_date_time,
    format_local_date_time_with_seconds,
    format_local_time,
)
from app.domain.model import Actor, Appointment, AppointmentStatus, Role
from app.domain.rules.names import subject_name
from app.domain.violations import Ok, Rejected, ValidationResult, Violation, ViolationCode

_TRANSITIONS: Mapping[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.RESERVED: frozenset({
        AppointmentStatus.CONFIRMED, AppointmentStatus.ATTENDED,
        AppointmentStatus.NO_SHOW, AppointmentStatus.CANCELLED,
    }),
    AppointmentStatus.CONFIRMED: frozenset({
        AppointmentStatus.ATTENDED, AppointmentStatus.NO_SHOW, AppointmentStatus.CANCELLED,
    }),
    AppointmentStatus.ATTENDED: frozenset(),
    AppointmentStatus.NO_SHOW: frozenset(),
    AppointmentStatus.CANCELLED: frozenset(),
}


def can_transition(origin: AppointmentStatus, target: AppointmentStatus) -> bool:
    """Indica si una arista pertenece al ciclo de vida ordinario."""
    return target in _TRANSITIONS[origin]


def cancel_appointment(
    appointment: Appointment,
    actor: Actor,
    now: datetime,
    professional_name: str,
    tz: ZoneInfo,
) -> ValidationResult:
    """Cancela un turno mediante una copia, sin borrar recursos ni leer el reloj."""
    now = _normalize_now(now)
    if actor.role is Role.ODONTOLOGO:
        description = _turn_description(appointment, professional_name, tz)
        return Rejected((
            Violation(
                ViolationCode.FORBIDDEN_OPERATION,
                f"No tiene permiso para cancelar el {description}: "
                "solo recepción y administración pueden cancelar turnos.",
            ),
        ))
    if not can_transition(appointment.status, AppointmentStatus.CANCELLED):
        return Rejected((
            _invalid_transition(appointment, AppointmentStatus.CANCELLED, professional_name, tz),
        ))
    return Ok(replace(appointment, status=AppointmentStatus.CANCELLED))


def change_status(
    appointment: Appointment,
    target: AppointmentStatus,
    actor: Actor,
    now: datetime,
    professional_name: str,
    tz: ZoneInfo,
) -> ValidationResult:
    """Cambia el estado ordinario mediante copia y la política única."""
    now = _normalize_now(now)
    if target is AppointmentStatus.CANCELLED:
        raise ValueError("Para cancelar debe usar cancel_appointment")
    if actor.role is Role.ODONTOLOGO and actor.professional_id != appointment.professional_id:
        description = _turn_description(appointment, professional_name, tz)
        return Rejected((
            Violation(
                ViolationCode.FORBIDDEN_OPERATION,
                f"No tiene permiso para cambiar el estado del {description}: "
                "un odontólogo solo puede cambiar el estado de sus propios turnos.",
            ),
        ))
    violations: list[Violation] = []
    if not can_transition(appointment.status, target):
        violations.append(_invalid_transition(appointment, target, professional_name, tz))
    if (
        target in (AppointmentStatus.ATTENDED, AppointmentStatus.NO_SHOW)
        and now < appointment.start_at
    ):
        violations.append(_too_early(appointment, target, now, professional_name, tz))
    if violations:
        return Rejected(tuple(violations))
    return Ok(replace(appointment, status=target))


def _too_early(
    appointment: Appointment, target: AppointmentStatus, now: datetime,
    professional_name: str, tz: ZoneInfo,
) -> Violation:
    return Violation(
        ViolationCode.STATUS_CHANGE_TOO_EARLY,
        f"El {_turn_description(appointment, professional_name, tz)} todavía no empezó: "
        f'no se puede marcar como "{target.value}" antes del inicio '
        f"(momento actual: {format_local_date_time_with_seconds(now, tz)}, hora local).",
    )


def _turn_description(appointment: Appointment, professional_name: str, tz: ZoneInfo) -> str:
    name = subject_name(professional_name, "el profesional")
    day = format_local_date_time(appointment.start_at, tz).split(" ")[0]
    start = format_local_time(appointment.start_at, tz)
    end = format_local_time(appointment.end_at, tz)
    return f"turno de {name} del {day} de {start} a {end} (hora local)"


def _invalid_transition(
    appointment: Appointment, target: AppointmentStatus, professional_name: str, tz: ZoneInfo,
) -> Violation:
    return Violation(
        ViolationCode.INVALID_TRANSITION,
        f'El {_turn_description(appointment, professional_name, tz)} no puede pasar '
        f'del estado "{appointment.status.value}" al estado "{target.value}".',
    )


def _normalize_now(now: datetime) -> datetime:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now necesita zona horaria (datetime naive)")
    return now.astimezone(timezone.utc)
