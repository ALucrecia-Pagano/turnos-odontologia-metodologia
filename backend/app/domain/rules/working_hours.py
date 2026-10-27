"""Reglas del horario de atencion de los profesionales (RN-AG-04, RN-DI-01, RN-DI-02).

Los tramos son intervalos semiabiertos `[inicio, fin)` en minutos locales desde las 00:00
(DD-07), con el dia de la semana ISO (1 = lunes ... 7 = domingo). Las reglas devuelven
violaciones y nunca lanzan excepciones por una regla de negocio.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Final
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_time, local_day_and_minutes
from app.domain.model import WorkingHours
from app.domain.violations import Violation, ViolationCode

_MINUTES_PER_DAY: Final = 1440
_WEEKDAY_NAMES: Final = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)
_WEEKDAY_NAMES_PLURAL: Final = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábados",
    "domingos",
)
_REASON_WEEKDAY: Final = "el día de la semana debe estar entre 1 (lunes) y 7 (domingo)"
_REASON_MINUTES: Final = "el inicio y el fin deben estar entre 00:00 y 24:00"
_REASON_ORDER: Final = "el inicio debe ser anterior al fin"


def _format_minute(minute: int) -> str:
    """Formatea minutos desde las 00:00 como `HH:MM` (1440 sale `24:00`)."""
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _join_with_and(items: Sequence[str]) -> str:
    """Une con `", "` y el ultimo con `" y "`."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} y {items[-1]}"


def _invalid_reasons(slot: WorkingHours) -> list[str]:
    """Razones por las que el tramo no es valido; vacia si lo es."""
    reasons: list[str] = []
    if not 1 <= slot.weekday <= len(_WEEKDAY_NAMES):
        reasons.append(_REASON_WEEKDAY)
    if not (
        0 <= slot.start_minute <= _MINUTES_PER_DAY and 0 <= slot.end_minute <= _MINUTES_PER_DAY
    ):
        reasons.append(_REASON_MINUTES)
    if slot.start_minute >= slot.end_minute:
        reasons.append(_REASON_ORDER)
    return reasons


def _overlaps(first: WorkingHours, second: WorkingHours) -> bool:
    """Indica si dos tramos validos del mismo profesional y dia comparten algun minuto."""
    return (
        first.professional_id == second.professional_id
        and first.weekday == second.weekday
        and first.start_minute < second.end_minute
        and second.start_minute < first.end_minute
    )


def validate_working_hours(slots: Sequence[WorkingHours]) -> list[Violation]:
    """Valida un conjunto de tramos del horario de atencion (RN-DI-01, RN-DI-02, US-010).

    Primero informa una `INVALID_WORKING_HOURS` por tramo invalido (dia fuera de 1..7,
    minutos fuera de 0..1440 o inicio no anterior al fin), aunque rompa mas de una
    condicion, en el orden recibido. Despues, con los tramos validos, informa una
    `OVERLAPPING_WORKING_HOURS` por cada par del mismo profesional y dia que comparten un
    minuto, ordenados por la posicion del primer tramo y luego la del segundo. Los tramos
    contiguos no se solapan y un tramo invalido no participa de los pares. Los tramos se
    identifican en los mensajes por su posicion, desde 1.

    Args:
        slots: Tramos de uno o varios profesionales, en el orden en que se cargaron.

    Returns:
        Las violaciones, o una lista vacia si el conjunto es valido.
    """
    violations: list[Violation] = []
    valid: list[tuple[int, WorkingHours]] = []
    for position, slot in enumerate(slots, start=1):
        reasons = _invalid_reasons(slot)
        if reasons:
            violations.append(
                Violation(
                    code=ViolationCode.INVALID_WORKING_HOURS,
                    message=f"El tramo {position} no es válido: {_join_with_and(reasons)}.",
                )
            )
        else:
            valid.append((position, slot))
    for index, (first_position, first) in enumerate(valid):
        for second_position, second in valid[index + 1 :]:
            if _overlaps(first, second):
                violations.append(
                    Violation(
                        code=ViolationCode.OVERLAPPING_WORKING_HOURS,
                        message=(
                            f"Los tramos {first_position} y {second_position} del "
                            f"{_WEEKDAY_NAMES[first.weekday - 1]} se solapan: de "
                            f"{_format_minute(first.start_minute)} a "
                            f"{_format_minute(first.end_minute)} y de "
                            f"{_format_minute(second.start_minute)} a "
                            f"{_format_minute(second.end_minute)}."
                        ),
                    )
                )
    return violations


def _merged_slots(slots: Sequence[WorkingHours]) -> list[tuple[int, int]]:
    """Une los tramos que se tocan o se pisan (RN-AG-04) y los ordena por inicio.

    Si el siguiente tramo empieza en el fin del anterior o antes, se extiende el fin al
    maximo de los dos; asi dos tramos contiguos cuentan como uno.

    Args:
        slots: Tramos de un mismo profesional y dia, en cualquier orden.

    Returns:
        Pares `(inicio, fin)` en minutos locales, ordenados y sin tramos que se toquen.
    """
    merged: list[tuple[int, int]] = []
    for slot in sorted(slots, key=lambda item: item.start_minute):
        if merged and slot.start_minute <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], slot.end_minute))
        else:
            merged.append((slot.start_minute, slot.end_minute))
    return merged


def _outside_message(
    start_at: datetime,
    end_at: datetime,
    weekday: int,
    merged: Sequence[tuple[int, int]],
    tz: ZoneInfo,
) -> str:
    """Arma el mensaje de `OUTSIDE_WORKING_HOURS` con los tramos unidos del dia."""
    prefix = (
        f"El turno de {format_local_time(start_at, tz)} a {format_local_time(end_at, tz)} "
        "(hora local) queda fuera del horario de atención del profesional: "
    )
    if not merged:
        return f"{prefix}no atiende los {_WEEKDAY_NAMES_PLURAL[weekday - 1]}."
    ranges = _join_with_and(
        [f"de {_format_minute(start)} a {_format_minute(end)}" for start, end in merged]
    )
    return f"{prefix}el {_WEEKDAY_NAMES[weekday - 1]} atiende {ranges}."


def check_working_hours(
    professional_id: UUID,
    start_at: datetime,
    end_at: datetime,
    working_hours: Sequence[WorkingHours],
    tz: ZoneInfo,
) -> list[Violation]:
    """Devuelve `OUTSIDE_WORKING_HOURS` si el turno no cae dentro del horario (RN-AG-04).

    El dominio elige los tramos del profesional y del dia de la semana local del inicio
    (RN-GL-03, DD-07): el llamador no necesita filtrarlos. Los tramos contiguos cuentan
    como uno. Un turno que termina a las 00:00 locales tiene su fin en el minuto 1440. Se
    supone que el turno ya cabe en un dia local (el grupo 1 rechaza el cruce de medianoche).

    Args:
        professional_id: Profesional del turno.
        start_at: Inicio del turno (instante con zona horaria).
        end_at: Fin del turno (instante con zona horaria).
        working_hours: Tramos de uno o varios profesionales.
        tz: Zona horaria en la que se evalua el horario.

    Returns:
        Lista vacia si el turno cae completo en un tramo; si no, una sola violacion sin
        turno en conflicto ni tipo de referencia.
    """
    day, start_minute = local_day_and_minutes(start_at, tz)
    end_day, end_minute = local_day_and_minutes(end_at, tz)
    if end_day == day + timedelta(days=1):
        end_minute = _MINUTES_PER_DAY
    weekday = day.isoweekday()
    merged = _merged_slots(
        [
            slot
            for slot in working_hours
            if slot.professional_id == professional_id and slot.weekday == weekday
        ]
    )
    if any(start <= start_minute and end_minute <= end for start, end in merged):
        return []
    return [
        Violation(
            code=ViolationCode.OUTSIDE_WORKING_HOURS,
            message=_outside_message(start_at, end_at, weekday, merged, tz),
        )
    ]
