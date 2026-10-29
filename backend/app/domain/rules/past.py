"""Regla del turno que no empieza en el pasado (RN-AG-06).

Un turno no puede empezar antes del momento actual. El momento actual (`now`) no se
lee del reloj: llega inyectado por el contexto (RN-GL-04) y se compara como instante.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_date_time, format_local_date_time_with_seconds
from app.domain.violations import Violation, ViolationCode


def _in_the_past_message(start_at: datetime, now: datetime, tz: ZoneInfo) -> str:
    return (
        f"El inicio del turno ({format_local_date_time(start_at, tz)}, hora local) es "
        f"anterior al momento actual ({format_local_date_time_with_seconds(now, tz)}, "
        "hora local): no se pueden dar turnos en el pasado."
    )


def check_not_in_the_past(start_at: datetime, now: datetime, tz: ZoneInfo) -> list[Violation]:
    """Devuelve una violacion `IN_THE_PAST` si el inicio es anterior al momento actual.

    La comparacion es estricta entre instantes, sin truncar `now` ni dar tolerancia
    (RN-AG-06, US-005 CA-1 a CA-3): un inicio igual a `now` es valido; con `now` 10:00:30
    un inicio 10:00 se rechaza, y tambien con un microsegundo de diferencia.

    Args:
        start_at: Inicio del turno (instante con zona horaria).
        now: Momento actual inyectado (instante con zona horaria).
        tz: Zona horaria para mostrar las horas del mensaje; no interviene en la
            comparacion.

    Returns:
        Lista vacia si el inicio no es anterior a `now`; si no, una sola violacion sin
        turno ni bloqueo en conflicto ni tipo de referencia. El mensaje muestra la fecha
        y hora locales del inicio (`dd/mm/aaaa HH:MM`) y del momento actual con segundos.
    """
    if start_at < now:
        return [
            Violation(
                code=ViolationCode.IN_THE_PAST,
                message=_in_the_past_message(start_at, now, tz),
            )
        ]
    return []
