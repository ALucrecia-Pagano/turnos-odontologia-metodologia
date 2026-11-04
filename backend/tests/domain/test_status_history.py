"""Tests del historial funcional de transiciones de estado del turno (C-12, RN-TU-06, US-033)."""

from datetime import datetime, timezone
from uuid import UUID

from app.domain.intervals import Interval
from app.domain.model import (
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    AppointmentStatusChange,
    RescheduleDetail,
    ScheduleContext,
)

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
S2 = UUID("00000000-0000-0000-0000-0000000000b2")
T1 = UUID("00000000-0000-0000-0000-0000000000f1")
U1 = UUID("00000000-0000-0000-0000-0000000000a1")
U2 = UUID("00000000-0000-0000-0000-0000000000a2")
U3 = UUID("00000000-0000-0000-0000-0000000000a3")

UTC = timezone.utc
NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)  # 09:00 hora local
T1_START = datetime(2026, 10, 20, 13, 0, tzinfo=UTC)  # 10:00 hora local
T1_END = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)  # 10:30 hora local
NEW_START = datetime(2026, 10, 20, 14, 0, tzinfo=UTC)  # 11:00 hora local
NEW_END = datetime(2026, 10, 20, 14, 30, tzinfo=UTC)  # 11:30 hora local


def test_reschedule_detail_and_status_change_keep_fields_for_creation_and_ordinary_transition() -> None:
    detail = RescheduleDetail(
        previous_interval=Interval(T1_START, T1_END),
        new_interval=Interval(NEW_START, NEW_END),
        previous_professional_id=P1,
        new_professional_id=P2,
        previous_chair_id=S1,
        new_chair_id=S2,
    )
    created_entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=None,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U2,
        changed_at=NOW,
    )
    confirmed_entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U2,
        changed_at=NOW,
    )

    assert detail.previous_interval == Interval(T1_START, T1_END)
    assert detail.new_interval == Interval(NEW_START, NEW_END)
    assert detail.previous_professional_id == P1
    assert detail.new_professional_id == P2
    assert detail.previous_chair_id == S1
    assert detail.new_chair_id == S2
    assert created_entry.appointment_id == T1
    assert created_entry.from_status is None
    assert created_entry.to_status is AppointmentStatus.RESERVED
    assert created_entry.changed_by == U2
    assert created_entry.changed_at == NOW
    assert created_entry.reschedule is None
    assert confirmed_entry.from_status is AppointmentStatus.RESERVED
    assert confirmed_entry.to_status is AppointmentStatus.CONFIRMED
    assert confirmed_entry.reschedule is None


def test_status_change_with_reschedule_detail_and_reexports() -> None:
    from app.domain import (
        AppointmentStatusChange as RootStatusChange,
        RescheduleDetail as RootRescheduleDetail,
    )
    from app.domain.appointment import (
        AppointmentStatusChange as ApptStatusChange,
        RescheduleDetail as ApptRescheduleDetail,
    )

    detail = RescheduleDetail(
        previous_interval=Interval(T1_START, T1_END),
        new_interval=Interval(NEW_START, NEW_END),
        previous_professional_id=P1,
        new_professional_id=P2,
        previous_chair_id=S1,
        new_chair_id=S2,
    )
    entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.CONFIRMED,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U3,
        changed_at=NOW,
        reschedule=detail,
    )

    assert entry.reschedule == detail
    assert RootStatusChange is AppointmentStatusChange
    assert ApptStatusChange is AppointmentStatusChange
    assert RootRescheduleDetail is RescheduleDetail
    assert ApptRescheduleDetail is RescheduleDetail



def test_status_change_naive_changed_at_raises_value_error() -> None:
    import pytest

    with pytest.raises(ValueError, match="changed_at.*zona horaria"):
        AppointmentStatusChange(
            appointment_id=T1,
            from_status=AppointmentStatus.RESERVED,
            to_status=AppointmentStatus.CONFIRMED,
            changed_by=U2,
            changed_at=datetime(2026, 10, 20, 9, 0),
        )


def test_status_change_normalizes_changed_at_to_utc() -> None:
    from datetime import timedelta

    buenos_aires = timezone(timedelta(hours=-3))
    entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U2,
        changed_at=datetime(2026, 10, 20, 9, 0, tzinfo=buenos_aires),
    )

    assert entry.changed_at == datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    assert entry.changed_at.utcoffset() == timedelta(0)
    assert entry.changed_at.tzinfo is UTC

    plus_two = timezone(timedelta(hours=2))
    entry_plus_two = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U2,
        changed_at=datetime(2026, 10, 20, 14, 0, tzinfo=plus_two),
    )
    assert entry_plus_two.changed_at == datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    assert entry_plus_two.changed_at.utcoffset() == timedelta(0)
    assert entry_plus_two.changed_at.tzinfo is UTC



def test_status_change_same_status_without_reschedule_raises_value_error() -> None:
    import pytest

    with pytest.raises(ValueError, match="reschedule"):
        AppointmentStatusChange(
            appointment_id=T1,
            from_status=AppointmentStatus.RESERVED,
            to_status=AppointmentStatus.RESERVED,
            changed_by=U2,
            changed_at=NOW,
            reschedule=None,
        )

    with pytest.raises(ValueError, match="reschedule"):
        AppointmentStatusChange(
            appointment_id=T1,
            from_status=AppointmentStatus.CONFIRMED,
            to_status=AppointmentStatus.CONFIRMED,
            changed_by=U2,
            changed_at=NOW,
            reschedule=None,
        )

    detail = RescheduleDetail(
        previous_interval=Interval(T1_START, T1_END),
        new_interval=Interval(NEW_START, NEW_END),
        previous_professional_id=P1,
        new_professional_id=P1,
        previous_chair_id=S1,
        new_chair_id=S1,
    )
    rescheduled_entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U2,
        changed_at=NOW,
        reschedule=detail,
    )
    assert rescheduled_entry.from_status is AppointmentStatus.RESERVED
    assert rescheduled_entry.to_status is AppointmentStatus.RESERVED
    assert rescheduled_entry.reschedule == detail



def test_appointment_status_change_is_immutable() -> None:
    from dataclasses import FrozenInstanceError
    import pytest

    entry = AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U2,
        changed_at=NOW,
    )
    for field_name, new_value in (
        ("appointment_id", P1),
        ("from_status", AppointmentStatus.CONFIRMED),
        ("to_status", AppointmentStatus.ATTENDED),
        ("changed_by", U3),
        ("changed_at", T1_START),
        ("reschedule", None),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(entry, field_name, new_value)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        setattr(entry, "extra_field", "forbidden")
    assert entry.appointment_id == T1
    assert entry.from_status is AppointmentStatus.RESERVED
    assert entry.to_status is AppointmentStatus.CONFIRMED
    assert entry.changed_by == U2
    assert entry.changed_at == NOW
    assert entry.reschedule is None


def test_reschedule_detail_is_immutable() -> None:
    from dataclasses import FrozenInstanceError
    import pytest

    detail = RescheduleDetail(
        previous_interval=Interval(T1_START, T1_END),
        new_interval=Interval(NEW_START, NEW_END),
        previous_professional_id=P1,
        new_professional_id=P1,
        previous_chair_id=S1,
        new_chair_id=S1,
    )
    for field_name, new_value in (
        ("previous_interval", Interval(NEW_START, NEW_END)),
        ("new_interval", Interval(T1_START, T1_END)),
        ("previous_professional_id", P2),
        ("new_professional_id", P2),
        ("previous_chair_id", S2),
        ("new_chair_id", S2),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(detail, field_name, new_value)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        setattr(detail, "extra_field", "forbidden")
    assert detail.previous_interval == Interval(T1_START, T1_END)
    assert detail.new_interval == Interval(NEW_START, NEW_END)
    assert detail.previous_professional_id == P1
    assert detail.new_professional_id == P1
    assert detail.previous_chair_id == S1
    assert detail.new_chair_id == S1


def _refs(
    *,
    professional_id: UUID = P1,
    professional_name: str = "Dra. Laura Quiroga",
    chair_id: UUID = S1,
    chair_name: str = "Sillón 1",
) -> AppointmentReferences:
    from app.domain.model import AppointmentReferences, Chair, Patient, Professional, Service

    return AppointmentReferences(
        patient=Patient(UUID("00000000-0000-0000-0000-0000000000c1"), "Ana Pérez", "30111222"),
        professional=Professional(professional_id, professional_name, active=True),
        chair=Chair(chair_id, chair_name, active=True),
        service=Service(UUID("00000000-0000-0000-0000-0000000000d1"), "Limpieza", 30),
    )


def _ctx(now: datetime = NOW) -> ScheduleContext:
    from zoneinfo import ZoneInfo
    from app.domain.model import ScheduleContext, WorkingHours

    return ScheduleContext(
        tz=ZoneInfo("America/Argentina/Buenos_Aires"),
        working_hours=(
            WorkingHours(P1, 2, 540, 1080),
            WorkingHours(P2, 2, 540, 1080),
        ),
        blocks=(),
        now=now,
    )


def test_validate_new_appointment_returns_creation_status_change() -> None:
    from app.domain.appointment import validate_new_appointment
    from app.domain.model import NewAppointmentRequest
    from app.domain.violations import Ok

    req = NewAppointmentRequest(
        id=T1,
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S1,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=T1_START,
        duration_min=30,
        changed_by=U2,
    )

    result = validate_new_appointment(req, _refs(), (), _ctx(NOW))

    assert isinstance(result, Ok)
    assert result.appointment.id == T1
    assert result.appointment.status is AppointmentStatus.RESERVED
    assert result.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=None,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U2,
        changed_at=NOW,
        reschedule=None,
    )

    later_now = datetime(2026, 10, 20, 12, 30, tzinfo=UTC)
    t2 = UUID("00000000-0000-0000-0000-0000000000f2")
    req_u3 = NewAppointmentRequest(
        id=t2,
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S1,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=NEW_START,
        duration_min=30,
        changed_by=U3,
    )
    result_u3 = validate_new_appointment(req_u3, _refs(), (), _ctx(later_now))
    assert isinstance(result_u3, Ok)
    assert result_u3.status_change == AppointmentStatusChange(
        appointment_id=t2,
        from_status=None,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U3,
        changed_at=later_now,
        reschedule=None,
    )


def test_validate_new_appointment_rejection_has_no_status_change() -> None:
    from app.domain.appointment import validate_new_appointment
    from app.domain.model import Appointment, NewAppointmentRequest
    from app.domain.violations import Rejected, ViolationCode

    existing = Appointment(
        id=T1,
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S1,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=T1_START,
        end_at=T1_END,
        status=AppointmentStatus.RESERVED,
    )
    req_overlap = NewAppointmentRequest(
        id=UUID("00000000-0000-0000-0000-0000000000f2"),
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S2,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=T1_START,
        duration_min=30,
        changed_by=U2,
    )

    rejected_overlap = validate_new_appointment(
        req_overlap,
        _refs(chair_id=S2, chair_name="Sillón 2"),
        (existing,),
        _ctx(NOW),
    )

    assert isinstance(rejected_overlap, Rejected)
    assert [v.code for v in rejected_overlap.violations] == [ViolationCode.PROFESSIONAL_OVERLAP]
    assert not hasattr(rejected_overlap, "status_change")

    past_start = datetime(2026, 10, 20, 12, 55, tzinfo=UTC)  # 09:55 local
    req_past = NewAppointmentRequest(
        id=UUID("00000000-0000-0000-0000-0000000000f3"),
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S1,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=past_start,
        duration_min=30,
        changed_by=U2,
    )
    rejected_past = validate_new_appointment(
        req_past,
        _refs(),
        (),
        _ctx(T1_START),
    )
    assert isinstance(rejected_past, Rejected)
    assert [v.code for v in rejected_past.violations] == [ViolationCode.IN_THE_PAST]
    assert rejected_past.violations[0].message == (
        "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento actual "
        "(20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado."
    )
    assert not hasattr(rejected_past, "status_change")


def _appt(
    status: AppointmentStatus = AppointmentStatus.RESERVED,
    *,
    professional_id: UUID = P1,
    chair_id: UUID = S1,
) -> Appointment:
    return Appointment(
        id=T1,
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=professional_id,
        chair_id=chair_id,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=T1_START,
        end_at=T1_END,
        status=status,
    )


def test_change_status_confirm_reserved_returns_status_change() -> None:
    from zoneinfo import ZoneInfo
    from app.domain.appointment import change_status
    from app.domain.model import Actor, Role
    from app.domain.violations import Ok

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    original = _appt(AppointmentStatus.RESERVED)
    actor = Actor(user_id=U2, role=Role.RECEPCION)

    result = change_status(
        original,
        AppointmentStatus.CONFIRMED,
        actor,
        NOW,
        "Dra. Laura Quiroga",
        tz,
    )

    assert isinstance(result, Ok)
    assert result.appointment.status is AppointmentStatus.CONFIRMED
    assert original.status is AppointmentStatus.RESERVED
    assert result.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U2,
        changed_at=NOW,
        reschedule=None,
    )

    admin = Actor(user_id=U3, role=Role.ADMINISTRADOR)
    local_now = datetime(2026, 10, 20, 9, 0, tzinfo=tz)
    result_admin = change_status(
        original,
        AppointmentStatus.CONFIRMED,
        admin,
        local_now,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(result_admin, Ok)
    assert result_admin.appointment.status is AppointmentStatus.CONFIRMED
    assert original.status is AppointmentStatus.RESERVED
    assert result_admin.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=U3,
        changed_at=NOW,
        reschedule=None,
    )
    assert result_admin.status_change.changed_at.tzinfo is UTC


def test_change_status_attended_and_no_show_return_status_change() -> None:
    from zoneinfo import ZoneInfo
    from app.domain.appointment import change_status
    from app.domain.model import Actor, Role
    from app.domain.violations import Ok

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    confirmed = _appt(AppointmentStatus.CONFIRMED)
    odontologist = Actor(user_id=U1, role=Role.ODONTOLOGO, professional_id=P1)

    attended_res = change_status(
        confirmed,
        AppointmentStatus.ATTENDED,
        odontologist,
        T1_START,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(attended_res, Ok)
    assert attended_res.appointment.status is AppointmentStatus.ATTENDED
    assert attended_res.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.CONFIRMED,
        to_status=AppointmentStatus.ATTENDED,
        changed_by=U1,
        changed_at=T1_START,
        reschedule=None,
    )

    reserved = _appt(AppointmentStatus.RESERVED)
    reception = Actor(user_id=U2, role=Role.RECEPCION)
    at_1015_utc = datetime(2026, 10, 20, 13, 15, tzinfo=UTC)
    no_show_res = change_status(
        reserved,
        AppointmentStatus.NO_SHOW,
        reception,
        at_1015_utc,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(no_show_res, Ok)
    assert no_show_res.appointment.status is AppointmentStatus.NO_SHOW
    assert no_show_res.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.NO_SHOW,
        changed_by=U2,
        changed_at=at_1015_utc,
        reschedule=None,
    )


def test_cancel_appointment_returns_status_change() -> None:
    from zoneinfo import ZoneInfo
    from app.domain.appointment import cancel_appointment
    from app.domain.model import Actor, Role
    from app.domain.violations import Ok

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    confirmed = _appt(AppointmentStatus.CONFIRMED)
    admin = Actor(user_id=U3, role=Role.ADMINISTRADOR)

    result = cancel_appointment(confirmed, admin, NOW, "Dra. Laura Quiroga", tz)

    assert isinstance(result, Ok)
    assert result.appointment.status is AppointmentStatus.CANCELLED
    assert confirmed.status is AppointmentStatus.CONFIRMED
    assert result.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.CONFIRMED,
        to_status=AppointmentStatus.CANCELLED,
        changed_by=U3,
        changed_at=NOW,
        reschedule=None,
    )

    reserved = _appt(AppointmentStatus.RESERVED)
    reception = Actor(user_id=U2, role=Role.RECEPCION)
    res_reserved = cancel_appointment(reserved, reception, NOW, "Dra. Laura Quiroga", tz)
    assert isinstance(res_reserved, Ok)
    assert res_reserved.appointment.status is AppointmentStatus.CANCELLED
    assert reserved.status is AppointmentStatus.RESERVED
    assert res_reserved.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.CANCELLED,
        changed_by=U2,
        changed_at=NOW,
        reschedule=None,
    )


def test_change_status_and_cancel_rejections_have_no_status_change() -> None:
    from zoneinfo import ZoneInfo
    from app.domain.appointment import cancel_appointment, change_status
    from app.domain.model import Actor, Role
    from app.domain.violations import Rejected, ViolationCode

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    reception = Actor(user_id=U2, role=Role.RECEPCION)
    other_odontologist = Actor(user_id=U1, role=Role.ODONTOLOGO, professional_id=P2)

    reserved = _appt(AppointmentStatus.RESERVED)
    too_early = change_status(
        reserved,
        AppointmentStatus.ATTENDED,
        reception,
        NOW,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(too_early, Rejected)
    assert [v.code for v in too_early.violations] == [ViolationCode.STATUS_CHANGE_TOO_EARLY]
    assert not hasattr(too_early, "status_change")
    assert reserved.status is AppointmentStatus.RESERVED

    forbidden_change = change_status(
        reserved,
        AppointmentStatus.CONFIRMED,
        other_odontologist,
        NOW,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(forbidden_change, Rejected)
    assert [v.code for v in forbidden_change.violations] == [ViolationCode.FORBIDDEN_OPERATION]
    assert not hasattr(forbidden_change, "status_change")

    attended = _appt(AppointmentStatus.ATTENDED)
    invalid_cancel = cancel_appointment(attended, reception, T1_END, "Dra. Laura Quiroga", tz)
    assert isinstance(invalid_cancel, Rejected)
    assert [v.code for v in invalid_cancel.violations] == [ViolationCode.INVALID_TRANSITION]
    assert not hasattr(invalid_cancel, "status_change")
    assert attended == _appt(AppointmentStatus.ATTENDED)

    cancelled = _appt(AppointmentStatus.CANCELLED)
    invalid_confirm = change_status(
        cancelled,
        AppointmentStatus.CONFIRMED,
        reception,
        NOW,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(invalid_confirm, Rejected)
    assert [v.code for v in invalid_confirm.violations] == [ViolationCode.INVALID_TRANSITION]
    assert not hasattr(invalid_confirm, "status_change")
    assert cancelled == _appt(AppointmentStatus.CANCELLED)

    forbidden_cancel = cancel_appointment(
        reserved,
        other_odontologist,
        NOW,
        "Dra. Laura Quiroga",
        tz,
    )
    assert isinstance(forbidden_cancel, Rejected)
    assert [v.code for v in forbidden_cancel.violations] == [ViolationCode.FORBIDDEN_OPERATION]
    assert not hasattr(forbidden_cancel, "status_change")


def test_reschedule_from_reserved_returns_single_status_change_with_detail() -> None:
    from app.domain.appointment import reschedule_appointment
    from app.domain.model import Actor, RescheduleRequest, Role
    from app.domain.violations import Ok

    original = _appt(AppointmentStatus.RESERVED)
    reception = Actor(user_id=U2, role=Role.RECEPCION)
    req = RescheduleRequest(start_at=NEW_START)

    result = reschedule_appointment(
        original,
        req,
        _refs(),
        (original,),
        reception,
        "Dra. Laura Quiroga",
        _ctx(NOW),
    )

    assert isinstance(result, Ok)
    assert result.appointment.id == T1
    assert result.appointment.status is AppointmentStatus.RESERVED
    assert result.status_change.from_status is not None
    assert result.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.RESERVED,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U2,
        changed_at=NOW,
        reschedule=RescheduleDetail(
            previous_interval=Interval(T1_START, T1_END),
            new_interval=Interval(NEW_START, NEW_END),
            previous_professional_id=P1,
            new_professional_id=P1,
            previous_chair_id=S1,
            new_chair_id=S1,
        ),
    )


def test_reschedule_from_confirmed_changing_resources_returns_status_change_with_detail() -> None:
    from app.domain.appointment import reschedule_appointment
    from app.domain.model import Actor, RescheduleRequest, Role
    from app.domain.violations import Ok

    original = _appt(AppointmentStatus.CONFIRMED, professional_id=P1, chair_id=S1)
    admin = Actor(user_id=U3, role=Role.ADMINISTRADOR)
    req = RescheduleRequest(
        start_at=NEW_START,
        professional_id=P2,
        chair_id=S2,
    )

    result = reschedule_appointment(
        original,
        req,
        _refs(
            professional_id=P2,
            professional_name="Dr. Martín Sosa",
            chair_id=S2,
            chair_name="Sillón 2",
        ),
        (original,),
        admin,
        "Dra. Laura Quiroga",
        _ctx(NOW),
    )

    assert isinstance(result, Ok)
    assert result.appointment.id == T1
    assert result.appointment.status is AppointmentStatus.RESERVED
    assert result.status_change.from_status is not None
    assert result.status_change == AppointmentStatusChange(
        appointment_id=T1,
        from_status=AppointmentStatus.CONFIRMED,
        to_status=AppointmentStatus.RESERVED,
        changed_by=U3,
        changed_at=NOW,
        reschedule=RescheduleDetail(
            previous_interval=Interval(T1_START, T1_END),
            new_interval=Interval(NEW_START, NEW_END),
            previous_professional_id=P1,
            new_professional_id=P2,
            previous_chair_id=S1,
            new_chair_id=S2,
        ),
    )


def test_reschedule_rejections_have_no_status_change() -> None:
    from app.domain.appointment import reschedule_appointment
    from app.domain.model import Actor, RescheduleRequest, Role
    from app.domain.violations import Rejected, ViolationCode

    original = _appt(AppointmentStatus.RESERVED)
    reception = Actor(user_id=U2, role=Role.RECEPCION)
    odontologist = Actor(user_id=U1, role=Role.ODONTOLOGO, professional_id=P1)
    req = RescheduleRequest(start_at=NEW_START)

    forbidden = reschedule_appointment(
        original,
        req,
        _refs(),
        (original,),
        odontologist,
        "Dra. Laura Quiroga",
        _ctx(NOW),
    )
    assert isinstance(forbidden, Rejected)
    assert [v.code for v in forbidden.violations] == [ViolationCode.FORBIDDEN_OPERATION]
    assert not hasattr(forbidden, "status_change")

    attended = _appt(AppointmentStatus.ATTENDED)
    invalid_state = reschedule_appointment(
        attended,
        req,
        _refs(),
        (attended,),
        reception,
        "Dra. Laura Quiroga",
        _ctx(NOW),
    )
    assert isinstance(invalid_state, Rejected)
    assert [v.code for v in invalid_state.violations] == [ViolationCode.INVALID_TRANSITION]
    assert not hasattr(invalid_state, "status_change")

    t3 = Appointment(
        id=UUID("00000000-0000-0000-0000-0000000000f3"),
        patient_id=UUID("00000000-0000-0000-0000-0000000000c1"),
        professional_id=P1,
        chair_id=S2,
        service_id=UUID("00000000-0000-0000-0000-0000000000d1"),
        start_at=NEW_START,
        end_at=NEW_END,
        status=AppointmentStatus.RESERVED,
    )
    overlap = reschedule_appointment(
        original,
        req,
        _refs(),
        (original, t3),
        reception,
        "Dra. Laura Quiroga",
        _ctx(NOW),
    )
    assert isinstance(overlap, Rejected)
    assert [v.code for v in overlap.violations] == [ViolationCode.PROFESSIONAL_OVERLAP]
    assert not hasattr(overlap, "status_change")
