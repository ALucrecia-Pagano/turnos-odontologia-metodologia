import pytest

from app.domain.rules.duration import check_duration
from app.domain.violations import Violation, ViolationCode


@pytest.mark.parametrize(
    ("duration", "message"),
    [
        (0, 'La duración del turno no es válida (se recibió 0 minutos): debe ser mayor que cero minutos.'),
        (-5, 'La duración del turno no es válida (se recibió -5 minutos): debe ser mayor que cero minutos.'),
        (7, 'La duración del turno no es válida (se recibió 7 minutos): debe ser múltiplo de 5 minutos.'),
        (485, 'La duración del turno no es válida (se recibió 485 minutos): no puede superar los 480 minutos.'),
        (487, 'La duración del turno no es válida (se recibió 487 minutos): debe ser múltiplo de 5 minutos y no puede superar los 480 minutos.'),
    ],
    ids=["zero", "negative", "grid", "maximum", "two-reasons"],
)
def test_duration_default_keeps_exact_c03_message(duration: int, message: str) -> None:
    assert check_duration(duration) == [Violation(ViolationCode.INVALID_DURATION, message)]
