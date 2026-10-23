"""Regla de duracion del turno (RN-AG-09, RN-DI-05 en la parte de la duracion).

La duracion efectiva debe ser mayor que cero, multiplo de 5 minutos y de 480 minutos
como maximo. Los limites son constantes del modulo (SU-02: "constante configurable"):
si el catalogo real necesita otro maximo, se cambia en un solo lugar.
"""

from typing import Final

from app.domain.rules.grid import GRID_STEP_MIN
from app.domain.violations import Violation, ViolationCode

MAX_DURATION_MIN: Final = 480


def check_duration(duration_min: int) -> list[Violation]:
    """Devuelve una violacion `INVALID_DURATION` si la duracion no es valida.

    Si se incumple mas de una condicion se informa una sola violacion cuyo mensaje las
    nombra todas. Para una duracion no positiva solo se informa esa razon (el multiplo
    de 5 no aporta nada para 0 o un negativo).

    Args:
        duration_min: Duracion efectiva en minutos.

    Returns:
        Lista vacia si la duracion es valida; si no, una sola violacion sin turno en
        conflicto.
    """
    reasons: list[str] = []
    if duration_min <= 0:
        reasons.append("debe ser mayor que cero minutos")
    elif duration_min % GRID_STEP_MIN != 0:
        reasons.append(f"debe ser múltiplo de {GRID_STEP_MIN} minutos")
    if duration_min > MAX_DURATION_MIN:
        reasons.append(f"no puede superar los {MAX_DURATION_MIN} minutos")
    if not reasons:
        return []
    return [
        Violation(
            code=ViolationCode.INVALID_DURATION,
            message=(
                f"La duración del turno no es válida (se recibió {duration_min} minutos): "
                f"{' y '.join(reasons)}."
            ),
        )
    ]
