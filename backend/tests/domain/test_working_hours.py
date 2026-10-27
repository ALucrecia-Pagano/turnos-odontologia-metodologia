from uuid import UUID

import pytest

from app.domain.model import WorkingHours
from app.domain.rules.working_hours import validate_working_hours
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
