from uuid import UUID

import pytest

from app.domain.violations import Rejected, Violation, ViolationCode

APPT_A = UUID("00000000-0000-0000-0000-0000000000a1")
APPT_B = UUID("00000000-0000-0000-0000-0000000000a2")


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
    ],
)
def test_violation_code_value_is_stable_api_code(code: ViolationCode, serialized: str) -> None:
    assert code.value == serialized


def test_violation_without_conflicting_appointment_defaults_to_none() -> None:
    violation = Violation(ViolationCode.INVALID_DURATION, "duracion invalida")

    assert violation.conflicting_appointment_id is None
