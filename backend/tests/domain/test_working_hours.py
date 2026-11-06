from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.model import Appointment, AppointmentStatus, WorkingHours
from app.domain.rules.working_hours import (
    appointments_outside_working_hours,
    validate_working_hours,
)
from app.domain.violations import ViolationCode

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")


def _codes(slots: list[WorkingHours]) -> list[ViolationCode]:
    return [violation.code for violation in validate_working_hours(slots)]


def test_validate_working_hours_start_equal_or_after_end_reports_one_invalid_per_slot() -> None:
    slots = [WorkingHours(P1, 2, 780, 780), WorkingHours(P1, 2, 800, 700)]

    assert _codes(slots) == [
        ViolationCode.INVALID_WORKING_HOURS,
        ViolationCode.INVALID_WORKING_HOURS,
    ]


@pytest.mark.parametrize(
    "slots",
    [
        [WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 900, 1140)],
        [WorkingHours(P1, 2, 1200, 1440)],
    ],
    ids=["varios-tramos-validos", "limite-del-dia"],
)
def test_validate_working_hours_valid_slots_report_nothing(slots: list[WorkingHours]) -> None:
    assert validate_working_hours(slots) == []


@pytest.mark.parametrize(
    "slot",
    [
        WorkingHours(P1, 2, -5, 60),
        WorkingHours(P1, 2, 0, 1445),
        WorkingHours(P1, 0, 540, 780),
        WorkingHours(P1, 8, 540, 780),
        WorkingHours(P1, 8, 800, 700),
    ],
    ids=["inicio-negativo", "fin-mayor-a-1440", "dia-0", "dia-8", "dia-8-e-inicio-posterior-al-fin"],
)
def test_validate_working_hours_out_of_range_slot_reports_exactly_one_invalid(
    slot: WorkingHours,
) -> None:
    assert _codes([slot]) == [ViolationCode.INVALID_WORKING_HOURS]


def test_validate_working_hours_overlapping_slots_same_day_report_one_overlap() -> None:
    slots = [WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 720, 900)]

    assert _codes(slots) == [ViolationCode.OVERLAPPING_WORKING_HOURS]


@pytest.mark.parametrize(
    "slots",
    [
        [WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 3, 720, 900)],
        [WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 780, 1020)],
        [WorkingHours(P1, 2, 540, 780), WorkingHours(P2, 2, 720, 900)],
    ],
    ids=["dias-distintos", "tramos-contiguos", "profesionales-distintos"],
)
def test_validate_working_hours_non_overlapping_slots_report_nothing(
    slots: list[WorkingHours],
) -> None:
    assert validate_working_hours(slots) == []


def test_validate_working_hours_set_reports_invalid_first_then_overlaps_by_position() -> None:
    slots = [
        WorkingHours(P1, 2, 540, 780),
        WorkingHours(P1, 2, 750, 750),
        WorkingHours(P1, 2, 720, 900),
        WorkingHours(P1, 2, 600, 660),
    ]

    violations = validate_working_hours(slots)

    assert [violation.code for violation in violations] == [
        ViolationCode.INVALID_WORKING_HOURS,
        ViolationCode.OVERLAPPING_WORKING_HOURS,
        ViolationCode.OVERLAPPING_WORKING_HOURS,
    ]
    assert "tramo 2" in violations[0].message
    assert "1 y 3" in violations[1].message
    assert "1 y 4" in violations[2].message


def test_validate_working_hours_invalid_slots_messages_name_the_position_without_references() -> None:
    violations = validate_working_hours([WorkingHours(P1, 2, 780, 780), WorkingHours(P1, 2, 800, 700)])

    assert "tramo 1" in violations[0].message
    assert "tramo 2" in violations[1].message
    for violation in violations:
        assert violation.conflicting_appointment_id is None
        assert violation.reference_kind is None


def test_validate_working_hours_overlap_message_names_positions_and_weekday() -> None:
    violations = validate_working_hours([WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 720, 900)])

    assert "tramos 1 y 2" in violations[0].message
    assert "martes" in violations[0].message
    assert violations[0].conflicting_appointment_id is None
    assert violations[0].reference_kind is None


@pytest.mark.parametrize(
    ("slot", "expected_message"),
    [
        (
            WorkingHours(P1, 2, 800, 700),
            "El tramo 1 no es válido: el inicio debe ser anterior al fin.",
        ),
        (
            WorkingHours(P1, 8, 540, 780),
            "El tramo 1 no es válido: el día de la semana debe estar entre 1 (lunes) y 7 (domingo).",
        ),
        (
            WorkingHours(P1, 2, -5, 60),
            "El tramo 1 no es válido: el inicio y el fin deben estar entre 00:00 y 24:00.",
        ),
        (
            WorkingHours(P1, 0, 0, 1445),
            "El tramo 1 no es válido: el día de la semana debe estar entre 1 (lunes) y 7 (domingo)"
            " y el inicio y el fin deben estar entre 00:00 y 24:00.",
        ),
    ],
    ids=["inicio-posterior-al-fin", "dia-fuera-de-rango", "minutos-fuera-de-rango", "dos-razones"],
)
def test_validate_working_hours_invalid_slot_message_lists_every_broken_condition(
    slot: WorkingHours, expected_message: str
) -> None:
    assert validate_working_hours([slot])[0].message == expected_message


def test_validate_working_hours_overlap_message_shows_both_ranges() -> None:
    violations = validate_working_hours([WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 720, 900)])

    assert violations[0].message == (
        "Los tramos 1 y 2 del martes se solapan: de 09:00 a 13:00 y de 12:00 a 15:00."
    )


def test_validate_working_hours_slot_breaking_three_conditions_joins_reasons_with_comma_and_y() -> (
    None
):
    violations = validate_working_hours([WorkingHours(P1, 0, 800, -5)])

    assert [violation.message for violation in violations] == [
        "El tramo 1 no es válido: el día de la semana debe estar entre 1 (lunes) y 7 (domingo), "
        "el inicio y el fin deben estar entre 00:00 y 24:00 y el inicio debe ser anterior al fin."
    ]


_CHAIR = UUID("00000000-0000-0000-0000-0000000000b1")
_PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
_SERVICE = UUID("00000000-0000-0000-0000-0000000000d1")
_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
_NOW = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)


def _apt(
    appointment_id: UUID,
    start_at: datetime,
    end_at: datetime,
    status: AppointmentStatus = AppointmentStatus.RESERVED,
    professional_id: UUID = P1,
) -> Appointment:
    return Appointment(
        id=appointment_id,
        patient_id=_PATIENT,
        professional_id=professional_id,
        chair_id=_CHAIR,
        service_id=_SERVICE,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )


def test_appointments_outside_working_hours_lists_future_occupying_appointment_outside_new_hours() -> None:
    t1 = _apt(
        UUID("00000000-0000-0000-0000-000000000071"),
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
        AppointmentStatus.RESERVED,
    )
    new_hours = [WorkingHours(professional_id=P1, weekday=1, start_minute=900, end_minute=1140)]

    result = appointments_outside_working_hours(P1, [t1], new_hours, _TZ, _NOW)

    assert result == [t1]
    assert t1.status == AppointmentStatus.RESERVED


def test_appointments_outside_working_hours_ignores_appointment_inside_new_hours() -> None:
    t1 = _apt(
        UUID("00000000-0000-0000-0000-000000000071"),
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
    )
    new_hours = [WorkingHours(professional_id=P1, weekday=1, start_minute=540, end_minute=780)]

    result = appointments_outside_working_hours(P1, [t1], new_hours, _TZ, _NOW)

    assert result == []


def test_appointments_outside_working_hours_ignores_cancelled_appointment() -> None:
    t2 = _apt(
        UUID("00000000-0000-0000-0000-000000000072"),
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
        status=AppointmentStatus.CANCELLED,
    )
    new_hours = [WorkingHours(professional_id=P1, weekday=1, start_minute=900, end_minute=1140)]

    result = appointments_outside_working_hours(P1, [t2], new_hours, _TZ, _NOW)

    assert result == []


def test_appointments_outside_working_hours_ignores_past_appointment() -> None:
    t3 = _apt(
        UUID("00000000-0000-0000-0000-000000000073"),
        datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 2, 13, 30, tzinfo=timezone.utc),
    )
    new_hours = [WorkingHours(professional_id=P1, weekday=1, start_minute=900, end_minute=1140)]

    result = appointments_outside_working_hours(P1, [t3], new_hours, _TZ, _NOW)

    assert result == []


def test_appointments_outside_working_hours_ignores_other_professional_appointments() -> None:
    t4 = _apt(
        UUID("00000000-0000-0000-0000-000000000074"),
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
        professional_id=P2,
    )

    result = appointments_outside_working_hours(P1, [t4], [], _TZ, _NOW)

    assert result == []


def test_appointments_outside_working_hours_returns_appointments_ordered_by_start_and_id() -> None:
    t5 = _apt(
        UUID("00000000-0000-0000-0000-000000000075"),
        datetime(2026, 12, 14, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 14, 13, 30, tzinfo=timezone.utc),
    )
    t6 = _apt(
        UUID("00000000-0000-0000-0000-000000000076"),
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
    )
    new_hours = [WorkingHours(professional_id=P1, weekday=1, start_minute=900, end_minute=1140)]

    result = appointments_outside_working_hours(P1, [t5, t6], new_hours, _TZ, _NOW)

    assert result == [t6, t5]
