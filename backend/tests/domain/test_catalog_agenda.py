from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.appointment import validate_new_appointment
from app.domain.catalog.activation import deactivate, reactivate
from app.domain.model import (
    Appointment, AppointmentReferences, AppointmentStatus, Chair, NewAppointmentRequest,
    Patient, Professional, ScheduleContext, Service, WorkingHours,
)
from app.domain.violations import Ok, ReferenceKind, Rejected, Violation, ViolationCode

P1 = UUID("00000000-0000-0000-0000-000000000001")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
SV1 = UUID("00000000-0000-0000-0000-0000000000d1")
PA1 = UUID("00000000-0000-0000-0000-0000000000c1")
T1 = UUID("00000000-0000-0000-0000-0000000000f1")
UTC = timezone.utc


def references() -> AppointmentReferences:
    return AppointmentReferences(
        Patient(PA1, "Ana Pérez", "30111222"),
        Professional(P1, "Dra. Laura Quiroga", True),
        Chair(S1, "Sillón 1", True),
        Service(SV1, "Limpieza", 45),
    )


def context() -> ScheduleContext:
    return ScheduleContext(
        ZoneInfo("America/Argentina/Buenos_Aires"), (WorkingHours(P1, 2, 0, 1440),), (),
        datetime(2026, 10, 1, tzinfo=UTC),
    )


def request() -> NewAppointmentRequest:
    return NewAppointmentRequest(T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC), 30)


def test_deactivate_professional_preserves_existing_appointment() -> None:
    appointment = Appointment(
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), AppointmentStatus.RESERVED,
    )
    inactive = deactivate(Professional(P1, "Dra. Laura Quiroga", True))
    assert inactive.active is False
    assert (
        appointment.id, appointment.patient_id, appointment.professional_id,
        appointment.chair_id, appointment.service_id, appointment.start_at,
        appointment.end_at, appointment.status.value,
    ) == (
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), "reservado",
    )


def test_deactivate_chair_preserves_existing_appointment() -> None:
    appointment = Appointment(
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), AppointmentStatus.RESERVED,
    )
    inactive = deactivate(Chair(S1, "Sillón 1", True))
    assert inactive.active is False
    assert (
        appointment.id, appointment.patient_id, appointment.professional_id,
        appointment.chair_id, appointment.service_id, appointment.start_at,
        appointment.end_at, appointment.status.value,
    ) == (
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), "reservado",
    )


def test_deactivate_service_preserves_existing_appointment() -> None:
    appointment = Appointment(
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), AppointmentStatus.RESERVED,
    )
    inactive = deactivate(Service(SV1, "Limpieza", 45))
    assert inactive.active is False
    assert (
        appointment.id, appointment.patient_id, appointment.professional_id,
        appointment.chair_id, appointment.service_id, appointment.start_at,
        appointment.end_at, appointment.status.value,
    ) == (
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), "reservado",
    )


def test_new_appointment_rejects_deactivated_professional() -> None:
    refs = replace(references(), professional=deactivate(Professional(P1, "Dra. Laura Quiroga", True)))
    assert validate_new_appointment(request(), refs, (), context()) == Rejected((
        Violation(ViolationCode.INACTIVE_REFERENCE, 'El profesional indicado está inactivo (id 00000000-0000-0000-0000-000000000001).', reference_kind=ReferenceKind.PROFESSIONAL),
    ))


def test_new_appointment_rejects_deactivated_chair() -> None:
    refs = replace(references(), chair=deactivate(Chair(S1, "Sillón 1", True)))
    assert validate_new_appointment(request(), refs, (), context()) == Rejected((
        Violation(ViolationCode.INACTIVE_REFERENCE, 'El sillón indicado está inactivo (id 00000000-0000-0000-0000-0000000000b1).', reference_kind=ReferenceKind.CHAIR),
    ))


def test_new_appointment_rejects_deactivated_service() -> None:
    refs = replace(references(), service=deactivate(Service(SV1, "Limpieza", 45)))
    assert validate_new_appointment(request(), refs, (), context()) == Rejected((
        Violation(ViolationCode.INACTIVE_REFERENCE, 'La prestación indicada está inactiva (id 00000000-0000-0000-0000-0000000000d1).', reference_kind=ReferenceKind.SERVICE),
    ))


def test_new_appointment_after_reactivation_keeps_agenda_ok_payload() -> None:
    professional = reactivate(deactivate(Professional(P1, "Dra. Laura Quiroga", True)))
    result = validate_new_appointment(request(), replace(references(), professional=professional), (), context())
    assert isinstance(result, Ok)
    assert result.appointment == Appointment(
        T1, PA1, P1, S1, SV1, datetime(2026, 10, 20, 13, tzinfo=UTC),
        datetime(2026, 10, 20, 13, 30, tzinfo=UTC), AppointmentStatus.RESERVED,
    )
