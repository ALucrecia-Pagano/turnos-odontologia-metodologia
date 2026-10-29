from uuid import UUID

import pytest

from app.domain.violations import ReferenceKind, Rejected, Violation, ViolationCode

APPT_A = UUID("00000000-0000-0000-0000-0000000000a1")
APPT_B = UUID("00000000-0000-0000-0000-0000000000a2")
BL1 = UUID("00000000-0000-0000-0000-0000000000e1")


def test_rejected_without_violations_raises_value_error() -> None:
    with pytest.raises(ValueError):
        Rejected(violations=())


@pytest.mark.parametrize(
    "ids",
    [
        [APPT_A],
        [APPT_B, APPT_A],
    ],
)
def test_rejected_keeps_violations_in_given_order(ids: list[UUID]) -> None:
    given = tuple(
        Violation(ViolationCode.PROFESSIONAL_OVERLAP, "conflicto", conflicting_appointment_id=i)
        for i in ids
    )

    rejected = Rejected(violations=given)

    assert [v.conflicting_appointment_id for v in rejected.violations] == ids


@pytest.mark.parametrize(
    ("code", "serialized"),
    [
        (ViolationCode.PROFESSIONAL_OVERLAP, "PROFESSIONAL_OVERLAP"),
        (ViolationCode.CHAIR_OVERLAP, "CHAIR_OVERLAP"),
        (ViolationCode.INVALID_DURATION, "INVALID_DURATION"),
        (ViolationCode.UNKNOWN_REFERENCE, "UNKNOWN_REFERENCE"),
        (ViolationCode.INACTIVE_REFERENCE, "INACTIVE_REFERENCE"),
        (ViolationCode.CROSSES_MIDNIGHT, "CROSSES_MIDNIGHT"),
        (ViolationCode.INVALID_START_TIME, "INVALID_START_TIME"),
        (ViolationCode.OUTSIDE_WORKING_HOURS, "OUTSIDE_WORKING_HOURS"),
        (ViolationCode.INVALID_WORKING_HOURS, "INVALID_WORKING_HOURS"),
        (ViolationCode.OVERLAPPING_WORKING_HOURS, "OVERLAPPING_WORKING_HOURS"),
        (ViolationCode.BLOCKED_TIME, "BLOCKED_TIME"),
        (ViolationCode.INVALID_BLOCK, "INVALID_BLOCK"),
        (ViolationCode.IN_THE_PAST, "IN_THE_PAST"),
    ],
)
def test_violation_code_value_is_stable_api_code(code: ViolationCode, serialized: str) -> None:
    assert code.value == serialized


def test_violation_without_conflicting_appointment_defaults_to_none() -> None:
    violation = Violation(ViolationCode.INVALID_DURATION, "duracion invalida")

    assert violation.conflicting_appointment_id is None


@pytest.mark.parametrize(
    ("kind", "serialized"),
    [
        (ReferenceKind.PATIENT, "PATIENT"),
        (ReferenceKind.PROFESSIONAL, "PROFESSIONAL"),
        (ReferenceKind.CHAIR, "CHAIR"),
        (ReferenceKind.SERVICE, "SERVICE"),
    ],
)
def test_reference_kind_value_is_stable_api_name(kind: ReferenceKind, serialized: str) -> None:
    assert kind.value == serialized


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (None, None),
        (ReferenceKind.CHAIR, ReferenceKind.CHAIR),
    ],
)
def test_violation_reference_kind_defaults_to_none_and_keeps_given_value(
    given: ReferenceKind | None, expected: ReferenceKind | None
) -> None:
    violation = Violation(ViolationCode.UNKNOWN_REFERENCE, "no existe", reference_kind=given)

    assert violation.reference_kind is expected


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (None, None),
        (BL1, BL1),
    ],
)
def test_violation_conflicting_block_id_defaults_to_none_and_keeps_given_value(
    given: UUID | None, expected: UUID | None
) -> None:
    violation = Violation(ViolationCode.BLOCKED_TIME, "bloqueado", conflicting_block_id=given)

    assert violation.conflicting_block_id == expected


def test_violation_built_as_in_c02_has_no_conflicting_block() -> None:
    violation = Violation(
        ViolationCode.PROFESSIONAL_OVERLAP, "conflicto", conflicting_appointment_id=APPT_A
    )

    assert violation.conflicting_block_id is None


def test_violation_built_as_in_c02_has_no_reference_kind() -> None:
    violation = Violation(ViolationCode.INVALID_DURATION, "duracion invalida")

    assert violation.reference_kind is None
