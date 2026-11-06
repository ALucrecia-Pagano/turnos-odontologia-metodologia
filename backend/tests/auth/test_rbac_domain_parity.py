"""La matriz coincide con lo que aplica el dominio, ejecutando las operaciones reales."""

from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.auth.permissions import PERMISSIONS, Action, Resource, Scope
from app.domain.appointment import (
    cancel_appointment,
    change_status,
    reschedule_appointment,
)
from app.domain.model import (
    Actor,
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    Chair,
    Patient,
    Professional,
    RescheduleRequest,
    Role,
    ScheduleContext,
    Service,
    WorkingHours,
)
from app.domain.violations import Rejected, ValidationResult, ViolationCode


UTC = timezone.utc
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
START = datetime(2026, 10, 20, 13, tzinfo=UTC)
END = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)
NEW_START = datetime(2026, 10, 20, 14, tzinfo=UTC)
PROFESSIONAL_OWN = UUID("00000000-0000-0000-0000-000000000001")
PROFESSIONAL_FOREIGN = UUID("00000000-0000-0000-0000-000000000002")
CHAIR = UUID("00000000-0000-0000-0000-0000000000b1")
SERVICE = UUID("00000000-0000-0000-0000-0000000000d1")
PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
APPOINTMENT = UUID("00000000-0000-0000-0000-0000000000f1")
NAME = "Dra. Laura Quiroga"

ACTORS = (
    Actor(UUID(int=11), Role.ODONTOLOGO, PROFESSIONAL_OWN),
    Actor(UUID(int=12), Role.RECEPCION),
    Actor(UUID(int=13), Role.ADMINISTRADOR),
)


def appointment(professional_id: UUID = PROFESSIONAL_OWN) -> Appointment:
    return Appointment(
        APPOINTMENT,
        PATIENT,
        professional_id,
        CHAIR,
        SERVICE,
        START,
        END,
        AppointmentStatus.RESERVED,
    )


def is_forbidden(result: ValidationResult) -> bool:
    return isinstance(result, Rejected) and any(
        violation.code is ViolationCode.FORBIDDEN_OPERATION
        for violation in result.violations
    )


def reschedule(actor: Actor) -> ValidationResult:
    return reschedule_appointment(
        appointment(),
        RescheduleRequest(start_at=NEW_START),
        AppointmentReferences(
            patient=Patient(PATIENT, "Ana Pérez", "30111222"),
            professional=Professional(PROFESSIONAL_OWN, NAME, active=True),
            chair=Chair(CHAIR, "Sillón 1", active=True),
            service=Service(SERVICE, "Limpieza", 45),
        ),
        [],
        actor,
        NAME,
        ScheduleContext(
            tz=TZ,
            working_hours=tuple(
                WorkingHours(PROFESSIONAL_OWN, day, 0, 1440) for day in range(1, 8)
            ),
            blocks=(),
            now=NOW,
        ),
    )


@pytest.mark.parametrize("actor", ACTORS, ids=lambda actor: actor.role.value)
def test_parity_reschedule(actor: Actor) -> None:
    row = PERMISSIONS[(Resource.APPOINTMENT, Action.RESCHEDULE)]

    assert is_forbidden(reschedule(actor)) is (actor.role not in row)


@pytest.mark.parametrize("actor", ACTORS, ids=lambda actor: actor.role.value)
def test_parity_cancel(actor: Actor) -> None:
    row = PERMISSIONS[(Resource.APPOINTMENT, Action.CANCEL)]

    result = cancel_appointment(appointment(), actor, NOW, NAME, TZ)

    assert is_forbidden(result) is (actor.role not in row)


@pytest.mark.parametrize("actor", ACTORS, ids=lambda actor: actor.role.value)
def test_parity_change_status_own(actor: Actor) -> None:
    row = PERMISSIONS[(Resource.APPOINTMENT, Action.CHANGE_STATUS)]

    result = change_status(
        appointment(PROFESSIONAL_OWN), AppointmentStatus.CONFIRMED, actor, NOW, NAME, TZ
    )

    assert actor.role in row
    assert is_forbidden(result) is False


@pytest.mark.parametrize("actor", ACTORS, ids=lambda actor: actor.role.value)
def test_parity_change_status_foreign(actor: Actor) -> None:
    row = PERMISSIONS[(Resource.APPOINTMENT, Action.CHANGE_STATUS)]

    result = change_status(
        appointment(PROFESSIONAL_FOREIGN), AppointmentStatus.CONFIRMED, actor, NOW, NAME, TZ
    )

    assert is_forbidden(result) is (row[actor.role] is Scope.OWN)
