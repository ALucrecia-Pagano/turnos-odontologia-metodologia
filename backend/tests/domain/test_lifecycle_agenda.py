"""Composición real de cancelación con alta de agenda y catálogo."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.appointment import cancel_appointment, validate_new_appointment
from app.domain.model import (
    Actor, Appointment, AppointmentReferences, AppointmentStatus as S, Chair,
    NewAppointmentRequest, Patient, Professional, Role, ScheduleContext, Service, WorkingHours,
)
from app.domain.violations import Ok, Rejected, ViolationCode as V

P1 = UUID("00000000-0000-0000-0000-000000000001")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
SV1 = UUID("00000000-0000-0000-0000-0000000000d1")
PA1 = UUID("00000000-0000-0000-0000-0000000000c1")
T1 = UUID("00000000-0000-0000-0000-0000000000f1")
T2 = UUID("00000000-0000-0000-0000-0000000000f2")
RECEPTION = Actor(UUID("00000000-0000-0000-0000-0000000000a2"), Role.RECEPCION)
UTC = timezone.utc
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
START = datetime(2026, 10, 20, 13, tzinfo=UTC)
END = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)


def original(status: S) -> Appointment:
    return Appointment(T1, PA1, P1, S1, SV1, START, END, status)


def references() -> AppointmentReferences:
    return AppointmentReferences(Patient(PA1, "Ana Pérez", "30111222"), Professional(P1, "Dra. Laura Quiroga", True), Chair(S1, "Sillón 1", True), Service(SV1, "Limpieza", 30))


def context() -> ScheduleContext:
    return ScheduleContext(TZ, (WorkingHours(P1, 2, 0, 1440),), (), NOW)


def request() -> NewAppointmentRequest:
    return NewAppointmentRequest(T2, PA1, P1, S1, SV1, START, 30)


def test_cancel_reserved_releases_both_resources() -> None:
    appointment = original(S.RESERVED)
    cancelled = cancel_appointment(appointment, RECEPTION, NOW, "Dra. Laura Quiroga", TZ)
    assert isinstance(cancelled, Ok)
    assert cancelled.appointment == replace(appointment, status=S.CANCELLED)
    result = validate_new_appointment(request(), references(), (cancelled.appointment,), context())
    assert result == Ok(Appointment(T2, PA1, P1, S1, SV1, START, END, S.RESERVED))
    assert appointment == original(S.RESERVED)


def test_cancel_confirmed_releases_both_resources() -> None:
    appointment = original(S.CONFIRMED)
    cancelled = cancel_appointment(appointment, RECEPTION, NOW, "Dra. Laura Quiroga", TZ)
    assert isinstance(cancelled, Ok)
    assert cancelled.appointment == replace(appointment, status=S.CANCELLED)
    result = validate_new_appointment(request(), references(), (cancelled.appointment,), context())
    assert result == Ok(Appointment(T2, PA1, P1, S1, SV1, START, END, S.RESERVED))
    assert appointment == original(S.CONFIRMED)


def test_before_cancellation_reserved_occupies_both() -> None:
    result = validate_new_appointment(request(), references(), (original(S.RESERVED),), context())
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.PROFESSIONAL_OVERLAP, V.CHAIR_OVERLAP]


def test_before_cancellation_confirmed_occupies_both() -> None:
    result = validate_new_appointment(request(), references(), (original(S.CONFIRMED),), context())
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.PROFESSIONAL_OVERLAP, V.CHAIR_OVERLAP]


def test_occupancy_regression_attended() -> None:
    result = validate_new_appointment(request(), references(), (original(S.ATTENDED),), context())
    assert isinstance(result, Rejected)
    assert [v.code for v in result.violations] == [V.PROFESSIONAL_OVERLAP, V.CHAIR_OVERLAP]


def test_occupancy_regression_no_show() -> None:
    result = validate_new_appointment(request(), references(), (original(S.NO_SHOW),), context())
    assert result == Ok(Appointment(T2, PA1, P1, S1, SV1, START, END, S.RESERVED))


def test_new_booking_and_catalog_keep_separate_payloads() -> None:
    from app.domain.catalog.create import create_professional
    from app.domain.catalog.result import Ok as CatalogOk

    result = validate_new_appointment(request(), references(), (), context())
    assert result == Ok(Appointment(T2, PA1, P1, S1, SV1, START, END, S.RESERVED))
    professional = Professional(P1, "Dra. Laura Quiroga", True)
    catalog = create_professional(professional)
    assert catalog == CatalogOk(professional)
    assert isinstance(catalog, CatalogOk)
    assert catalog.entity == professional
