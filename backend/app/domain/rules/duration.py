"""Regla de duracion del turno (RN-AG-09, parcial: solo duracion positiva)."""

from app.domain.violations import Violation, ViolationCode


def check_positive_duration(duration_min: int) -> list[Violation]:
    """Devuelve una violacion `INVALID_DURATION` si la duracion no es positiva.

    Args:
        duration_min: Duracion efectiva en minutos.

    Returns:
        Lista vacia si `duration_min > 0`; si no, una sola violacion sin turno en conflicto.
    """
    if duration_min > 0:
        return []
    return [
        Violation(
            code=ViolationCode.INVALID_DURATION,
            message=f"La duración del turno debe ser mayor que cero minutos (se recibió {duration_min}).",
        )
    ]
