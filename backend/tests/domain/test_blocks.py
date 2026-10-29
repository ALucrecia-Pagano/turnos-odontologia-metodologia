from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.model import Appointment, AppointmentStatus, Block
from app.domain.rules.blocks import appointments_affected_by_block, validate_block
from app.domain.violations import ViolationCode

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
SVC = UUID("00000000-0000-0000-0000-0000000000d1")
T1 = UUID("00000000-0000-0000-0000-000000000071")
T2 = UUID("00000000-0000-0000-0000-000000000072")
T3 = UUID("00000000-0000-0000-0000-000000000073")
T4 = UUID("00000000-0000-0000-0000-000000000074")
T5 = UUID("00000000-0000-0000-0000-000000000075")
T6 = UUID("00000000-0000-0000-0000-000000000076")
T7 = UUID("00000000-0000-0000-0000-000000000077")
BL1 = UUID("00000000-0000-0000-0000-0000000000e1")

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")


def _local(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 20, hour, minute, tzinfo=BUENOS_AIRES)


def _block(start_at: datetime, end_at: datetime) -> Block:
    return Block(id=BL1, professional_id=P1, start_at=start_at, end_at=end_at)


def test_validate_block_start_equal_to_end_reports_invalid_block() -> None:
    # 10:00 a 10:00 hora local = 13:00 a 13:00 UTC
    block = _block(_local(10), _local(10))

    assert [violation.code for violation in validate_block(block)] == [
        ViolationCode.INVALID_BLOCK
    ]


@pytest.mark.parametrize(
    ("start_at", "end_at", "expected"),
    [
        # 12:00 a 10:00 hora local = 15:00 a 13:00 UTC
        (_local(12), _local(10), [ViolationCode.INVALID_BLOCK]),
        # BL1: 10:00 a 12:00 hora local = 13:00 a 15:00 UTC
        (_local(10), _local(12), []),
        # 10:00 a 10:01 hora local = 13:00 a 13:01 UTC: los bloqueos no tienen grilla
        (_local(10), _local(10, 1), []),
    ],
    ids=["inicio-posterior-al-fin", "bloqueo-valido", "un-minuto-fuera-de-la-grilla"],
)
def test_validate_block_reports_invalid_only_when_start_is_not_before_end(
    start_at: datetime, end_at: datetime, expected: list[ViolationCode]
) -> None:
    block = _block(start_at, end_at)

    assert [violation.code for violation in validate_block(block)] == expected


def test_validate_block_message_says_start_must_be_before_end_without_conflicting_ids() -> None:
    [violation] = validate_block(_block(_local(10), _local(10)))

    assert violation.message == "El bloqueo no es válido: el inicio debe ser anterior al fin."
    assert violation.conflicting_appointment_id is None
    assert violation.conflicting_block_id is None
    assert violation.reference_kind is None


def _appointment(
    id: UUID,
    start_at: datetime,
    end_at: datetime,
    status: AppointmentStatus = AppointmentStatus.RESERVED,
    professional_id: UUID = P1,
) -> Appointment:
    return Appointment(
        id=id,
        patient_id=PATIENT,
        professional_id=professional_id,
        chair_id=S1,
        service_id=SVC,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )


# Turnos del requisito "Turnos afectados por un bloqueo", todos del 2026-10-20 (hora local).
APPOINTMENTS = {
    # 09:30 a 10:00 = 12:30 a 13:00 UTC: termina cuando empieza BL1
    "T1": _appointment(T1, _local(9, 30), _local(10)),
    # 10:30 a 11:00 = 13:30 a 14:00 UTC
    "T2": _appointment(T2, _local(10, 30), _local(11), AppointmentStatus.CONFIRMED),
    # 11:45 a 12:15 = 14:45 a 15:15 UTC
    "T3": _appointment(T3, _local(11, 45), _local(12, 15)),
    # 11:00 a 11:30 = 14:00 a 14:30 UTC, cancelado
    "T4": _appointment(T4, _local(11), _local(11, 30), AppointmentStatus.CANCELLED),
    # 10:00 a 10:30 = 13:00 a 13:30 UTC, ausente
    "T5": _appointment(T5, _local(10), _local(10, 30), AppointmentStatus.NO_SHOW),
    # 10:30 a 11:00 = 13:30 a 14:00 UTC, de otro profesional
    "T6": _appointment(T6, _local(10, 30), _local(11), professional_id=P2),
    # 12:00 a 12:30 = 15:00 a 15:30 UTC: empieza cuando termina BL1
    "T7": _appointment(T7, _local(12), _local(12, 30)),
}


def _bl1() -> Block:
    # BL1: P1 de 10:00 a 12:00 hora local = 13:00 a 15:00 UTC
    return _block(_local(10), _local(12))


def test_appointments_affected_by_block_returns_active_overlapping_of_same_professional() -> None:
    given = [APPOINTMENTS[name] for name in ("T7", "T6", "T5", "T4", "T3", "T2", "T1")]

    affected = appointments_affected_by_block(_bl1(), given)

    assert [appointment.id for appointment in affected] == [T2, T3]


def test_appointments_affected_by_block_without_overlapping_returns_empty() -> None:
    given = [APPOINTMENTS["T1"], APPOINTMENTS["T6"], APPOINTMENTS["T7"]]

    assert appointments_affected_by_block(_bl1(), given) == []


def test_appointments_affected_by_block_returns_them_unchanged() -> None:
    given = list(APPOINTMENTS.values())

    affected = appointments_affected_by_block(_bl1(), given)

    t2, t3 = affected
    assert (t2.status, t3.status) == (AppointmentStatus.CONFIRMED, AppointmentStatus.RESERVED)
    assert (t2.start_at.isoformat(), t2.end_at.isoformat()) == (
        "2026-10-20T13:30:00+00:00",
        "2026-10-20T14:00:00+00:00",
    )
    assert (t3.start_at.isoformat(), t3.end_at.isoformat()) == (
        "2026-10-20T14:45:00+00:00",
        "2026-10-20T15:15:00+00:00",
    )
    assert (t2.professional_id, t2.chair_id, t3.professional_id, t3.chair_id) == (P1, S1, P1, S1)
    assert t2 is APPOINTMENTS["T2"] and t3 is APPOINTMENTS["T3"]


def test_appointments_affected_by_invalid_block_returns_empty_without_raising() -> None:
    # 12:00 a 10:00 hora local: inicio posterior al fin
    invalid = _block(_local(12), _local(10))

    assert appointments_affected_by_block(invalid, list(APPOINTMENTS.values())) == []
