"""Intervalos semiabiertos `[start, end)` y deteccion de solapamiento."""

from dataclasses import dataclass
from datetime import datetime


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
