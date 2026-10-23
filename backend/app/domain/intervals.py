"""Intervalos semiabiertos `[start, end)`, solapamiento y hora local."""

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class Interval:
    """Intervalo semiabierto `[start, end)`.

    Attributes:
        start: Inicio (incluido).
        end: Fin (excluido).

    Raises:
        ValueError: Si `start >= end`.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("start debe ser anterior a end")


def overlaps(a: Interval, b: Interval) -> bool:
    """Indica si dos intervalos semiabiertos se solapan.

    Que uno termine justo cuando empieza el otro no es solapamiento.
    """
    return a.start < b.end and b.start < a.end


def _to_local(instant: datetime, tz: ZoneInfo) -> datetime:
    """Convierte el instante a la zona `tz`; un instante naive es un error de programacion."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("instant necesita zona horaria (datetime naive)")
    return instant.astimezone(tz)


def local_day_and_minutes(instant: datetime, tz: ZoneInfo) -> tuple[date, int]:
    """Convierte un instante a la zona recibida y devuelve el dia local y los minutos.

    La zona se recibe por parametro: el dominio no fija ninguna (SU-01). Los instantes
    se guardan en UTC (DD-07) y la hora local se calcula solo para evaluar reglas.

    Args:
        instant: Instante con zona horaria.
        tz: Zona horaria en la que se mide el dia local.

    Returns:
        El dia local y los minutos desde las 00:00 de ese dia (`hora * 60 + minuto`;
        los segundos se descartan).

    Raises:
        ValueError: Si `instant` no tiene zona horaria (error de programacion).
    """
    local = _to_local(instant, tz)
    return local.date(), local.hour * 60 + local.minute


def format_local_time(instant: datetime, tz: ZoneInfo) -> str:
    """Devuelve la hora local del instante para usar en mensajes.

    La zona se recibe por parametro (SU-01).

    Args:
        instant: Instante con zona horaria.
        tz: Zona horaria en la que se muestra la hora.

    Returns:
        `HH:MM` o, si hay segundos o microsegundos distintos de cero, `HH:MM:SS`
        (los microsegundos no se muestran).

    Raises:
        ValueError: Si `instant` no tiene zona horaria (error de programacion).
    """
    local = _to_local(instant, tz)
    if local.second or local.microsecond:
        return local.strftime("%H:%M:%S")
    return local.strftime("%H:%M")
