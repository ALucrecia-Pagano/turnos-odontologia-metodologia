"""Operación de reprogramar un turno: literales ficticios de la spec C-11 (RN-TU-03, US-031)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.model import (
    Actor,
    Appointment,
    AppointmentReferences,
    AppointmentStatus as S,
    Block,
    Chair,
    Patient,
    Professional,
    RescheduleRequest,
    Role,
    ScheduleContext,
    Service,
    WorkingHours,
)
from app.domain.violations import Ok, Rejected, Violation, ViolationCode as V

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
P3 = UUID("00000000-0000-0000-0000-000000000003")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
S2 = UUID("00000000-0000-0000-0000-0000000000b2")
SVC = UUID("00000000-0000-0000-0000-0000000000d1")
PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
T1 = UUID("00000000-0000-0000-0000-0000000000f1")
T2 = UUID("00000000-0000-0000-0000-0000000000f2")
T3 = UUID("00000000-0000-0000-0000-0000000000f3")
T4 = UUID("00000000-0000-0000-0000-0000000000f4")
BL1 = UUID("00000000-0000-0000-0000-0000000000e1")
U1 = UUID("00000000-0000-0000-0000-0000000000a1")
U2 = UUID("00000000-0000-0000-0000-0000000000a2")
U3 = UUID("00000000-0000-0000-0000-0000000000a3")

UTC = timezone.utc
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)  # 09:00 hora local
T1_START = datetime(2026, 10, 20, 13, tzinfo=UTC)  # 10:00 hora local
T1_END = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)  # 10:30 hora local
RESTART = datetime(2026, 10, 20, 14, tzinfo=UTC)  # 11:00 hora local
REEND = datetime(2026, 10, 20, 14, 30, tzinfo=UTC)  # 11:30 hora local

P1_NAME = "Dra. Laura Quiroga"
S1_NAME = "Sillón 1"
P2_NAME = "Dra. Inés Molina"
S2_NAME = "Sillón 2"

FULL_WEEK = tuple(WorkingHours(p, d, 0, 1440) for p in (P1, P2) for d in range(1, 8))
RECEPTION = Actor(U2, Role.RECEPCION)
ADMIN = Actor(U3, Role.ADMINISTRADOR)
DENTIST = Actor(U1, Role.ODONTOLOGO, P1)


def _service(default: int = 45) -> Service:
    return Service(SVC, "Limpieza", default)


def _appointment(
    status: S = S.RESERVED,
    *,
    id: UUID = T1,
    professional_id: UUID = P1,
    chair_id: UUID = S1,
    start_at: datetime = T1_START,
    end_at: datetime = T1_END,
    service_id: UUID = SVC,
) -> Appointment:
    return Appointment(id, PATIENT, professional_id, chair_id, service_id, start_at, end_at, status)


def _existing(
    id: UUID,
    professional_id: UUID,
    chair_id: UUID,
    start_at: datetime,
    end_at: datetime,
    status: S = S.RESERVED,
) -> Appointment:
    return Appointment(id, PATIENT, professional_id, chair_id, SVC, start_at, end_at, status)


def _refs(
    *,
    patient: Patient | None = Patient(PATIENT, "Ana Pérez", "30111222"),
    professional: Professional | None = Professional(P1, P1_NAME, active=True),
    chair: Chair | None = Chair(S1, S1_NAME, active=True),
    service: Service | None = _service(),
) -> AppointmentReferences:
    return AppointmentReferences(patient=patient, professional=professional, chair=chair, service=service)


def _ctx(
    *,
    now: datetime = NOW,
    working_hours: tuple[WorkingHours, ...] = FULL_WEEK,
    blocks: tuple[Block, ...] = (),
) -> ScheduleContext:
    return ScheduleContext(tz=TZ, working_hours=working_hours, blocks=blocks, now=now)


def _reschedule(
    start_at: datetime = RESTART,
    *,
    professional_id: UUID | None = None,
    chair_id: UUID | None = None,
    duration_min: int | None = None,
) -> RescheduleRequest:
    return RescheduleRequest(
        start_at=start_at,
        professional_id=professional_id,
        chair_id=chair_id,
        duration_min=duration_min,
    )


def test_reschedule_valid_keeps_id_and_returns_reserved() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment()
    result = reschedule_appointment(original, _reschedule(), _refs(), [], RECEPTION, P1_NAME, _ctx())

    assert result == Ok(
        Appointment(T1, PATIENT, P1, S1, SVC, RESTART, REEND, S.RESERVED)
    )
    assert original == _appointment()


def test_reschedule_from_confirmed_returns_reserved() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment(S.CONFIRMED)
    result = reschedule_appointment(original, _reschedule(), _refs(), [], RECEPTION, P1_NAME, _ctx())

    assert isinstance(result, Ok)
    assert result.appointment.status is S.RESERVED
    assert result.appointment.id == T1
    assert original == _appointment(S.CONFIRMED)


def test_reschedule_valid_original_unchanged() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment()
    reschedule_appointment(original, _reschedule(), _refs(), [], RECEPTION, P1_NAME, _ctx())

    assert original == _appointment()


@pytest.mark.parametrize("status", [S.ATTENDED, S.NO_SHOW, S.CANCELLED])
def test_reschedule_terminal_status_returns_dedicated_violation(status: S) -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(status), _reschedule(), _refs(), [], RECEPTION, P1_NAME, _ctx()
    )

    assert result == Rejected(
        (
            Violation(
                V.INVALID_TRANSITION,
                f'El turno de {P1_NAME} del 20/10/2026 de 10:00 a 10:30 (hora local) '
                f'no se puede reprogramar porque está en estado terminal "{status.value}".',
            ),
        )
    )


def test_reschedule_terminal_status_does_not_change_original() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment(S.ATTENDED)
    reschedule_appointment(original, _reschedule(), _refs(), [], RECEPTION, P1_NAME, _ctx())

    assert original == _appointment(S.ATTENDED)


@pytest.mark.parametrize("target_id", [T1, T2])
def test_dentist_cannot_reschedule_any_appointment(target_id: UUID) -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment(professional_id=P1 if target_id == T1 else P2, id=target_id)
    result = reschedule_appointment(
        original, _reschedule(), _refs(), [], DENTIST, P1_NAME, _ctx()
    )

    assert isinstance(result, Rejected)
    assert result.violations == (
        Violation(
            V.FORBIDDEN_OPERATION,
            f"No tiene permiso para reprogramar el turno de {P1_NAME} del 20/10/2026 "
            "de 10:00 a 10:30 (hora local): solo recepción y administración pueden reprogramar turnos.",
        ),
    )


@pytest.mark.parametrize("actor", [RECEPTION, ADMIN])
def test_reception_and_administration_can_reschedule(actor: Actor) -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(), _reschedule(), _refs(), [], actor, P1_NAME, _ctx()
    )

    assert isinstance(result, Ok)


def test_reschedule_permission_precedes_terminal_status_and_slot() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(S.ATTENDED),
        _reschedule(start_at=datetime(2026, 10, 20, 11, tzinfo=TZ)),
        _refs(),
        [],
        DENTIST,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert [violation.code for violation in result.violations] == [V.FORBIDDEN_OPERATION]


def test_reschedule_status_precedes_slot_conflicts() -> None:
    from app.domain.appointment import reschedule_appointment

    conflict = _existing(T3, P1, S2, RESTART, REEND)
    result = reschedule_appointment(
        _appointment(S.CANCELLED),
        _reschedule(),
        _refs(),
        [conflict],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert [violation.code for violation in result.violations] == [V.INVALID_TRANSITION]


def test_reschedule_excludes_itself_from_overlaps() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment()
    result = reschedule_appointment(
        original,
        _reschedule(start_at=datetime(2026, 10, 20, 13, 15, tzinfo=UTC)),
        _refs(),
        [original],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Ok)


def test_reschedule_can_change_only_professional_without_self_chair_conflict() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(
            start_at=T1_START,
            professional_id=P2,
        ),
        _refs(professional=Professional(P2, P2_NAME, active=True)),
        [_appointment()],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Ok)
    assert result.appointment.professional_id == P2


def test_reschedule_keeps_real_duration_when_omitted() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(), _reschedule(), _refs(service=_service(45)), [], RECEPTION, P1_NAME, _ctx()
    )

    assert isinstance(result, Ok)
    assert result.appointment.end_at == REEND


def test_reschedule_uses_requested_duration() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(duration_min=60),
        _refs(),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(now=datetime(2026, 10, 20, 13, tzinfo=UTC)),
    )

    assert isinstance(result, Ok)
    assert result.appointment.end_at == datetime(2026, 10, 20, 15, tzinfo=UTC)


def test_reschedule_rejects_professional_overlap_with_existing_appointment() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(),
        _refs(),
        [_existing(T3, P1, S2, RESTART, REEND)],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.PROFESSIONAL_OVERLAP
    assert result.violations[0].conflicting_appointment_id == T3


def test_reschedule_rejects_chair_overlap_with_existing_appointment() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(),
        _refs(),
        [_existing(T4, P2, S1, RESTART, REEND)],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.CHAIR_OVERLAP
    assert result.violations[0].conflicting_appointment_id == T4


def test_reschedule_rejects_past_with_reprogramar_message() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(start_at=datetime(2026, 10, 20, 9, tzinfo=TZ)),
        _refs(),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(now=datetime(2026, 10, 20, 13, tzinfo=UTC)),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].message.endswith(
        "no se pueden reprogramar turnos en el pasado."
    )


def test_reschedule_rejects_unknown_new_professional() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(professional_id=P3),
        _refs(professional=None),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.UNKNOWN_REFERENCE
    assert result.violations[0].reference_kind is not None
    assert result.violations[0].reference_kind.name == "PROFESSIONAL"


def test_reschedule_rejects_inactive_service_from_original_references() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(),
        _refs(service=Service(SVC, "Limpieza", 45, active=False)),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.INACTIVE_REFERENCE


def test_reschedule_rejects_naive_context_now() -> None:
    with pytest.raises(ValueError, match="now necesita zona horaria"):
        ScheduleContext(tz=TZ, working_hours=FULL_WEEK, blocks=(), now=datetime(2026, 10, 20, 9))


def test_reschedule_rejects_outside_working_hours() -> None:
    from app.domain.appointment import reschedule_appointment

    hours = tuple(WorkingHours(P1, day, 540, 660) for day in range(1, 8))
    result = reschedule_appointment(
        _appointment(),
        _reschedule(),
        _refs(),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(working_hours=hours),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.OUTSIDE_WORKING_HOURS


def test_reschedule_rejects_blocked_slot() -> None:
    from app.domain.appointment import reschedule_appointment

    block = Block(BL1, P1, RESTART, datetime(2026, 10, 20, 15, tzinfo=UTC))
    result = reschedule_appointment(
        _appointment(),
        _reschedule(),
        _refs(),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(blocks=(block,)),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.BLOCKED_TIME
    assert result.violations[0].conflicting_block_id == BL1


def test_reschedule_rejects_same_minute_past_with_seconds() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(start_at=datetime(2026, 10, 20, 10, tzinfo=TZ)),
        _refs(),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(now=datetime(2026, 10, 20, 13, 0, 30, tzinfo=UTC)),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].message == (
        "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento actual "
        "(20/10/2026 10:00:30, hora local): no se pueden reprogramar turnos en el pasado."
    )


def test_reschedule_rejects_inactive_new_professional() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(professional_id=P2),
        _refs(professional=Professional(P2, P2_NAME, active=False)),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.INACTIVE_REFERENCE


def test_reschedule_rejects_inactive_new_chair() -> None:
    from app.domain.appointment import reschedule_appointment

    result = reschedule_appointment(
        _appointment(),
        _reschedule(chair_id=S2),
        _refs(chair=Chair(S2, S2_NAME, active=False)),
        [],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is V.INACTIVE_REFERENCE


def test_reschedule_rejection_does_not_change_original() -> None:
    from app.domain.appointment import reschedule_appointment

    original = _appointment()
    result = reschedule_appointment(
        original,
        _reschedule(),
        _refs(),
        [_existing(T3, P1, S2, RESTART, REEND)],
        RECEPTION,
        P1_NAME,
        _ctx(),
    )

    assert isinstance(result, Rejected)
    assert original == _appointment()
