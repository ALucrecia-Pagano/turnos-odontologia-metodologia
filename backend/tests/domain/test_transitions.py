"""Política ordinaria con oráculo independiente de RN-TU-02."""

import pytest

from app.domain.model import AppointmentStatus as S


@pytest.mark.parametrize("origin", list(S))
@pytest.mark.parametrize("target", list(S))
def test_all_25_pairs_independent_oracle(origin: S, target: S) -> None:
    from app.domain.appointment.transitions import can_transition

    # Propiedades de RN-TU-02: no se importa ni reconstruye la tabla productiva.
    if origin is target or target is S.RESERVED:
        expected = False
    elif origin is S.RESERVED:
        expected = True
    elif origin is S.CONFIRMED:
        expected = target not in (S.RESERVED, S.CONFIRMED)
    else:
        expected = False
    assert can_transition(origin, target) is expected


def test_reserved_can_be_confirmed() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.RESERVED, S.CONFIRMED) is True


def test_reserved_can_be_attended() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.RESERVED, S.ATTENDED) is True


def test_reserved_can_be_no_show() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.RESERVED, S.NO_SHOW) is True


def test_reserved_can_be_cancelled() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.RESERVED, S.CANCELLED) is True


def test_confirmed_can_be_attended() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.CONFIRMED, S.ATTENDED) is True


def test_confirmed_can_be_no_show() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.CONFIRMED, S.NO_SHOW) is True


def test_confirmed_can_be_cancelled() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.CONFIRMED, S.CANCELLED) is True


def test_confirmed_cannot_return_reserved() -> None:
    from app.domain.appointment.transitions import can_transition

    assert can_transition(S.CONFIRMED, S.RESERVED) is False
