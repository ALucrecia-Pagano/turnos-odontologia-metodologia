"""Regla de turno dentro de un solo dia local (RN-AG-10, SU-09).

Inicio y fin deben caer en el mismo dia local. Por el intervalo semiabierto `[inicio, fin)`
(DD-07), un turno que termina justo a las 00:00 locales no ocupa el dia siguiente y es
valido. La comparacion usa el fin completo, sin truncar a minutos. La zona se recibe por
parametro (SU-01): la regla no se evalua sobre UTC.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domain.intervals import format_local_time, local_day_and_minutes
from app.domain.violations import Violation, ViolationCode


def check_same_local_day(start_at: datetime, end_at: datetime, tz: ZoneInfo) -> list[Violation]:
    """Devuelve una violacion `CROSSES_MIDNIGHT` si el turno cruza la medianoche local.

    Se compara el instante completo del fin, con segundos y fracciones, contra las 00:00
    locales del dia siguiente al del inicio: cruza la medianoche si el fin es posterior
    (un fin a las 00:00:30 cruza; un fin exacto a las 00:00 es valido).

    Args:
        start_at: Inicio del turno (instante con zona horaria).
        end_at: Fin del turno (instante con zona horaria).
        tz: Zona horaria en la que se evalua el dia local.

    Returns:
        Lista vacia si el turno cabe en un dia local; si no, una sola violacion sin turno
        en conflicto ni tipo de referencia.
    """
    start_day, _ = local_day_and_minutes(start_at, tz)
    next_midnight = datetime.combine(start_day + timedelta(days=1), time.min, tzinfo=tz)
    if end_at.astimezone(tz) > next_midnight:
        return [
            Violation(
                code=ViolationCode.CROSSES_MIDNIGHT,
                message=(
                    "El turno no puede cruzar la medianoche: empieza a las "
                    f"{format_local_time(start_at, tz)} y termina a las "
                    f"{format_local_time(end_at, tz)} del día siguiente (hora local)."
                ),
            )
        ]
    return []
