from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.intervals import Interval
from app.domain.model import (
    Appointment,
    AppointmentStatus,
    Block,
    NewAppointmentRequest,
    ScheduleContext,
    WorkingHours,
)

APPT_NEW = UUID("00000000-0000-0000-0000-0000000000f1")
BL1 = UUID("00000000-0000-0000-0000-0000000000e1")
PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
P1 = UUID("00000000-0000-0000-0000-000000000001")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
SVC = UUID("00000000-0000-0000-0000-0000000000d1")

UTC = timezone.utc
ZONE = ZoneInfo("America/Argentina/Buenos_Aires")
BUENOS_AIRES = timezone(timedelta(hours=-3))


def _request(start_at: datetime) -> NewAppointmentRequest:
    return NewAppointmentRequest(
        id=APPT_NEW,
        patient_id=PATIENT,
        professional_id=P1,
        chair_id=S1,
        service_id=SVC,
        start_at=start_at,
    )


def _appointment(
    start_at: datetime,
    end_at: datetime,
    status: AppointmentStatus = AppointmentStatus.RESERVED,
) -> Appointment:
    return Appointment(
        id=APPT_NEW,
        patient_id=PATIENT,
        professional_id=P1,
        chair_id=S1,
        service_id=SVC,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )


def test_new_appointment_request_start_without_timezone_raises_value_error() -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        _request(datetime(2026, 10, 20, 13, 0))


@pytest.mark.parametrize(
    ("start_at", "end_at"),
    [
        (datetime(2026, 10, 20, 13, 0), datetime(2026, 10, 20, 13, 30, tzinfo=UTC)),
        (datetime(2026, 10, 20, 13, 0, tzinfo=UTC), datetime(2026, 10, 20, 13, 30)),
    ],
)
def test_appointment_instant_without_timezone_raises_value_error(
    start_at: datetime, end_at: datetime
) -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        _appointment(start_at, end_at)


@pytest.mark.parametrize(
    ("given", "expected_start_iso", "expected_end_iso"),
    [
        (
            datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES),
            "2026-10-20T13:00:00+00:00",
            "2026-10-20T13:30:00+00:00",
        ),
        (
            datetime(2026, 10, 20, 13, 0, tzinfo=UTC),
            "2026-10-20T13:00:00+00:00",
            "2026-10-20T13:30:00+00:00",
        ),
    ],
)
def test_instants_with_timezone_are_normalized_to_utc(
    given: datetime, expected_start_iso: str, expected_end_iso: str
) -> None:
    request = _request(given)
    appointment = _appointment(given, given + timedelta(minutes=30))

    assert request.start_at.isoformat() == expected_start_iso
    assert appointment.start_at.isoformat() == expected_start_iso
    assert appointment.end_at.isoformat() == expected_end_iso
    for normalized in (request.start_at, appointment.start_at, appointment.end_at):
        assert normalized.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("start_at", "end_at"),
    [
        (datetime(2026, 10, 20, 13, 0, tzinfo=UTC), datetime(2026, 10, 20, 13, 0, tzinfo=UTC)),
        (datetime(2026, 10, 20, 13, 30, tzinfo=UTC), datetime(2026, 10, 20, 13, 0, tzinfo=UTC)),
    ],
)
def test_appointment_start_not_before_end_raises_value_error(
    start_at: datetime, end_at: datetime
) -> None:
    with pytest.raises(ValueError, match="anterior"):
        _appointment(start_at, end_at)


def test_appointment_interval_spans_start_to_end_in_utc() -> None:
    appointment = _appointment(
        datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES),
        datetime(2026, 10, 20, 10, 30, tzinfo=BUENOS_AIRES),
    )

    assert appointment.interval == Interval(
        datetime(2026, 10, 20, 13, 0, tzinfo=UTC), datetime(2026, 10, 20, 13, 30, tzinfo=UTC)
    )


@pytest.mark.parametrize(
    ("weekday", "start_minute", "end_minute"),
    [
        (0, 800, 700),
        (8, -5, 1445),
    ],
)
def test_working_hours_with_invalid_values_is_built_without_raising(
    weekday: int, start_minute: int, end_minute: int
) -> None:
    slot = WorkingHours(P1, weekday, start_minute, end_minute)

    assert (slot.weekday, slot.start_minute, slot.end_minute) == (weekday, start_minute, end_minute)


def test_block_loaded_in_buenos_aires_time_is_normalized_to_utc() -> None:
    block = Block(
        id=BL1,
        professional_id=P1,
        start_at=datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES),
        end_at=datetime(2026, 10, 20, 12, 0, tzinfo=BUENOS_AIRES),
    )

    assert block.start_at.isoformat() == "2026-10-20T13:00:00+00:00"
    assert block.end_at.isoformat() == "2026-10-20T15:00:00+00:00"


@pytest.mark.parametrize(
    ("start_at", "end_at"),
    [
        (datetime(2026, 10, 20, 10, 0), datetime(2026, 10, 20, 12, 0, tzinfo=BUENOS_AIRES)),
        (datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES), datetime(2026, 10, 20, 12, 0)),
    ],
    ids=["inicio-naive", "fin-naive"],
)
def test_block_instant_without_timezone_raises_value_error(
    start_at: datetime, end_at: datetime
) -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        Block(id=BL1, professional_id=P1, start_at=start_at, end_at=end_at)


def test_block_with_start_after_end_is_built_without_raising() -> None:
    block = Block(
        id=BL1,
        professional_id=P1,
        start_at=datetime(2026, 10, 20, 12, 0, tzinfo=BUENOS_AIRES),
        end_at=datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES),
        reason="feriado",
    )

    assert block.start_at > block.end_at


def _context(now: datetime) -> ScheduleContext:
    return ScheduleContext(tz=ZONE, working_hours=(), blocks=(), now=now)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        pytest.param(
            datetime(2026, 10, 20, 10, 0, tzinfo=BUENOS_AIRES),
            datetime(2026, 10, 20, 13, 0, tzinfo=UTC),
            id="buenos-aires",
        ),
        pytest.param(
            datetime(2026, 10, 20, 14, 0, tzinfo=timezone(timedelta(hours=1))),
            datetime(2026, 10, 20, 13, 0, tzinfo=UTC),
            id="mas-uno",
        ),
    ],
)
def test_schedule_context_now_with_zone_is_normalized_to_utc(
    now: datetime, expected: datetime
) -> None:
    context = _context(now)

    assert context.now == expected
    assert context.now.utcoffset() == timedelta(0)


def test_schedule_context_now_without_timezone_raises_value_error() -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        _context(datetime(2026, 10, 20, 10, 0))
