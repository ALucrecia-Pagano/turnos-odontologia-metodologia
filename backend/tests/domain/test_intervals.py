from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.domain.intervals import Interval, format_local_time, local_day_and_minutes, overlaps

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")


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


def test_local_day_and_minutes_utc_instant_on_previous_local_day_returns_previous_day() -> None:
    instant = datetime(2026, 10, 20, 2, 30, tzinfo=timezone.utc)

    assert local_day_and_minutes(instant, BUENOS_AIRES) == (date(2026, 10, 19), 1410)


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        pytest.param(
            datetime(2026, 10, 21, 3, 0, tzinfo=timezone.utc),
            (date(2026, 10, 21), 0),
            id="medianoche-local",
        ),
        pytest.param(
            datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            (date(2026, 10, 20), 600),
            id="diez-de-la-manana",
        ),
        pytest.param(
            datetime(2026, 10, 20, 13, 5, 30, tzinfo=timezone.utc),
            (date(2026, 10, 20), 605),
            id="descarta-segundos",
        ),
    ],
)
def test_local_day_and_minutes_follows_table(instant: datetime, expected: tuple[date, int]) -> None:
    assert local_day_and_minutes(instant, BUENOS_AIRES) == expected


def test_local_day_and_minutes_naive_instant_raises_value_error() -> None:
    with pytest.raises(ValueError):
        local_day_and_minutes(datetime(2026, 10, 20, 13, 0), BUENOS_AIRES)


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        pytest.param(datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc), "23:30", id="23-30"),
        pytest.param(datetime(2026, 10, 21, 3, 30, tzinfo=timezone.utc), "00:30", id="00-30"),
        pytest.param(datetime(2026, 10, 20, 12, 5, tzinfo=timezone.utc), "09:05", id="ceros"),
    ],
)
def test_format_local_time_without_seconds_returns_hh_mm(instant: datetime, expected: str) -> None:
    assert format_local_time(instant, BUENOS_AIRES) == expected


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        pytest.param(
            datetime(2026, 10, 20, 13, 5, 30, tzinfo=timezone.utc), "10:05:30", id="con-segundos"
        ),
        pytest.param(
            datetime(2026, 10, 20, 13, 5, 0, 250000, tzinfo=timezone.utc),
            "10:05:00",
            id="solo-microsegundos",
        ),
    ],
)
def test_format_local_time_with_seconds_or_microseconds_returns_hh_mm_ss(
    instant: datetime, expected: str
) -> None:
    assert format_local_time(instant, BUENOS_AIRES) == expected


def test_format_local_time_naive_instant_raises_value_error() -> None:
    with pytest.raises(ValueError):
        format_local_time(datetime(2026, 10, 20, 13, 0), BUENOS_AIRES)
