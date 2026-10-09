from datetime import datetime, timezone

import pytest

from app.domain.intervals import Interval, overlaps


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 20, hour, minute, tzinfo=timezone.utc)


def _interval(start: tuple[int, int], end: tuple[int, int]) -> Interval:
    return Interval(_at(*start), _at(*end))


# Intervalo base: 13:00-14:00.
OVERLAP_CASES = [
    pytest.param((12, 0), (15, 0), True, id="contiene"),
    pytest.param((13, 15), (13, 45), True, id="contenido"),
    pytest.param((12, 30), (13, 30), True, id="cruce-por-izquierda"),
    pytest.param((13, 30), (14, 30), True, id="cruce-por-derecha"),
    pytest.param((13, 0), (14, 0), True, id="igual"),
    pytest.param((12, 0), (13, 0), False, id="consecutivo-por-izquierda"),
    pytest.param((14, 0), (15, 0), False, id="consecutivo-por-derecha"),
    pytest.param((9, 0), (10, 0), False, id="disjunto"),
]


@pytest.mark.parametrize(("start", "end", "expected"), OVERLAP_CASES)
def test_overlaps_half_open_intervals_follow_table(
    start: tuple[int, int], end: tuple[int, int], expected: bool
) -> None:
    base = _interval((13, 0), (14, 0))

    assert overlaps(base, _interval(start, end)) is expected


@pytest.mark.parametrize(("start", "end", "expected"), OVERLAP_CASES)
def test_overlaps_is_symmetric(
    start: tuple[int, int], end: tuple[int, int], expected: bool
) -> None:
    base = _interval((13, 0), (14, 0))

    assert overlaps(_interval(start, end), base) is expected


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ((13, 0), (13, 0)),
        ((14, 0), (13, 0)),
    ],
)
def test_interval_start_not_before_end_raises_value_error(
    start: tuple[int, int], end: tuple[int, int]
) -> None:
    with pytest.raises(ValueError):
        _interval(start, end)
