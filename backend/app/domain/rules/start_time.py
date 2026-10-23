"""Regla del inicio del turno en la grilla (RN-DI-05 en la parte del inicio).

En hora local, los minutos del inicio deben ser multiplo de `GRID_STEP_MIN` y los
segundos y microsegundos deben ser cero. La granularidad es la misma que la de la
duracion (SU-02) y la zona se recibe por parametro (SU-01).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_time
from app.domain.rules.grid import GRID_STEP_MIN
from app.domain.violations import Violation, ViolationCode


def check_start_time(start_at: datetime, tz: ZoneInfo) -> list[Violation]:
    """Devuelve una violacion `INVALID_START_TIME` si el inicio no esta en la grilla.

    Si se incumple mas de una condicion (minutos y segundos) se informa una sola
    violacion cuyo mensaje las nombra todas. La hora del mensaje es la local.

    Args:
        start_at: Inicio del turno (instante con zona horaria).
        tz: Zona horaria en la que se evalua la grilla.

    Returns:
        Lista vacia si el inicio esta en la grilla; si no, una sola violacion sin turno
        en conflicto ni tipo de referencia.
    """
    local = start_at.astimezone(tz)
    reasons: list[str] = []
    if local.minute % GRID_STEP_MIN != 0:
        reasons.append(f"debe caer en un minuto múltiplo de {GRID_STEP_MIN}")
    if local.second != 0 or local.microsecond != 0:
        reasons.append("no puede tener segundos ni fracciones de segundo")
    if not reasons:
        return []
    return [
        Violation(
            code=ViolationCode.INVALID_START_TIME,
            message=(
                f"El inicio del turno no es válido (se recibió {format_local_time(start_at, tz)}, "
                f"hora local): {' y '.join(reasons)}."
            ),
        )
    ]
