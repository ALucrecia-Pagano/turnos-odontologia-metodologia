from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from app.domain.appointment import validate_new_appointment
from app.domain.model import (
    Appointment,
    AppointmentReferences,
    AppointmentStatus,
    Block,
    Chair,
    NewAppointmentRequest,
    Patient,
    Professional,
    ScheduleContext,
    Service,
    WorkingHours,
)
from app.domain.violations import Ok, ReferenceKind, Rejected, Violation, ViolationCode

PATIENT = UUID("00000000-0000-0000-0000-0000000000c1")
P1 = UUID("00000000-0000-0000-0000-000000000001")
S1 = UUID("00000000-0000-0000-0000-0000000000b1")
SVC_30 = UUID("00000000-0000-0000-0000-0000000000d1")
T_NEW = UUID("00000000-0000-0000-0000-0000000000f1")
P2 = UUID("00000000-0000-0000-0000-000000000002")
S2 = UUID("00000000-0000-0000-0000-0000000000b2")
S3 = UUID("00000000-0000-0000-0000-0000000000b3")
APPT_A = UUID("00000000-0000-0000-0000-0000000000a1")
APPT_B = UUID("00000000-0000-0000-0000-0000000000a2")
APPT_C = UUID("00000000-0000-0000-0000-0000000000a3")
APPT_D = UUID("00000000-0000-0000-0000-0000000000a4")
APPT_E = UUID("00000000-0000-0000-0000-0000000000a5")
APPT_F = UUID("00000000-0000-0000-0000-0000000000a6")
BL1 = UUID("00000000-0000-0000-0000-0000000000e1")
BL2 = UUID("00000000-0000-0000-0000-0000000000e2")
BL3 = UUID("00000000-0000-0000-0000-0000000000e3")
BLV = UUID("00000000-0000-0000-0000-0000000000e4")

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")
EARLY_NOW = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
FULL_WEEK = tuple(WorkingHours(p, d, 0, 1440) for p in (P1, P2) for d in range(1, 8))
CTX = ScheduleContext(tz=BUENOS_AIRES, working_hours=FULL_WEEK, blocks=(), now=EARLY_NOW)
TUESDAY_BASE = (WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 900, 1140))


def _ctx(*slots: WorkingHours) -> ScheduleContext:
    return ScheduleContext(tz=BUENOS_AIRES, working_hours=slots, blocks=(), now=EARLY_NOW)


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 20, hour, minute, tzinfo=timezone.utc)


def _local(day: int, hour: int, minute: int, second: int = 0, microsecond: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, second, microsecond, tzinfo=BUENOS_AIRES)


def _existing(
    id: UUID,
    professional_id: UUID,
    chair_id: UUID,
    start_at: datetime,
    end_at: datetime,
    status: AppointmentStatus = AppointmentStatus.RESERVED,
) -> Appointment:
    return Appointment(
        id=id,
        patient_id=PATIENT,
        professional_id=professional_id,
        chair_id=chair_id,
        service_id=SVC_30,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )


def _appt_a() -> Appointment:
    return _existing(APPT_A, P1, S1, _at(13), _at(13, 30))


def _refs(
    *,
    patient: Patient | None = Patient(PATIENT),
    professional: Professional | None = Professional(P1, active=True),
    chair: Chair | None = Chair(S1, active=True),
    service: Service | None = Service(SVC_30, 30),
) -> AppointmentReferences:
    return AppointmentReferences(
        patient=patient, professional=professional, chair=chair, service=service
    )


def _request(
    start_at: datetime,
    *,
    id: UUID = T_NEW,
    professional_id: UUID = P1,
    chair_id: UUID = S1,
    duration_min: int | None = None,
) -> NewAppointmentRequest:
    return NewAppointmentRequest(
        id=id,
        patient_id=PATIENT,
        professional_id=professional_id,
        chair_id=chair_id,
        service_id=SVC_30,
        start_at=start_at,
        duration_min=duration_min,
    )


def test_validate_new_appointment_all_references_existing_and_active_returns_ok() -> None:
    result = validate_new_appointment(_request(_at(13)), _refs(), [], CTX)

    assert result == Ok(
        Appointment(
            id=T_NEW,
            patient_id=PATIENT,
            professional_id=P1,
            chair_id=S1,
            service_id=SVC_30,
            start_at=_at(13),
            end_at=_at(13, 30),
            status=AppointmentStatus.RESERVED,
        )
    )


def test_validate_new_appointment_free_professional_and_chair_returns_ok_with_reserved_appointment() -> (
    None
):
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(_request(_at(13)), _refs(service=service), [], CTX)

    assert result == Ok(
        Appointment(
            id=T_NEW,
            patient_id=PATIENT,
            professional_id=P1,
            chair_id=S1,
            service_id=SVC_30,
            start_at=_at(13),
            end_at=_at(13, 30),
            status=AppointmentStatus.RESERVED,
        )
    )


def _ok_end(result: object) -> datetime:
    assert isinstance(result, Ok)
    return result.appointment.end_at


def test_validate_new_appointment_explicit_duration_replaces_service_default() -> None:
    service = Service(id=SVC_30, default_duration_min=45)

    result = validate_new_appointment(_request(_at(13), duration_min=20), _refs(service=service), [], CTX)

    assert _ok_end(result) == _at(13, 20)


@pytest.mark.parametrize(
    ("default_min", "explicit_min", "expected_end"),
    [
        (45, None, _at(13, 45)),
        (45, 20, _at(13, 20)),
        (0, 30, _at(13, 30)),
    ],
)
def test_validate_new_appointment_effective_duration_sets_end(
    default_min: int, explicit_min: int | None, expected_end: datetime
) -> None:
    service = Service(id=SVC_30, default_duration_min=default_min)

    result = validate_new_appointment(
        _request(_at(13), duration_min=explicit_min), _refs(service=service), [], CTX
    )

    assert _ok_end(result) == expected_end


def test_validate_new_appointment_start_in_buenos_aires_time_returns_utc_appointment() -> None:
    service = Service(id=SVC_30, default_duration_min=30)
    start_local = datetime(2026, 10, 20, 10, 0, tzinfo=timezone(timedelta(hours=-3)))

    result = validate_new_appointment(_request(start_local), _refs(service=service), [], CTX)

    assert isinstance(result, Ok)
    assert result.appointment.start_at.isoformat() == "2026-10-20T13:00:00+00:00"
    assert result.appointment.end_at.isoformat() == "2026-10-20T13:30:00+00:00"


def _summary(result: object) -> list[tuple[ViolationCode, UUID | None]]:
    assert isinstance(result, Rejected)
    return [(v.code, v.conflicting_appointment_id) for v in result.violations]


def test_validate_new_appointment_explicit_zero_duration_is_rejected_as_invalid_duration() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(_request(_at(13), duration_min=0), _refs(service=service), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


@pytest.mark.parametrize(
    ("default_min", "explicit_min"),
    [
        (30, -15),
        (0, None),
        (-30, None),
    ],
)
def test_validate_new_appointment_non_positive_effective_duration_is_rejected(
    default_min: int, explicit_min: int | None
) -> None:
    service = Service(id=SVC_30, default_duration_min=default_min)

    result = validate_new_appointment(
        _request(_at(13), duration_min=explicit_min), _refs(service=service), [], CTX
    )

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_invalid_duration_message_mentions_received_value() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(
        _request(_at(13), duration_min=-15), _refs(service=service), [], CTX
    )

    assert isinstance(result, Rejected)
    assert "-15" in result.violations[0].message
    assert result.violations[0].message == (
        "La duración del turno no es válida (se recibió -15 minutos): debe ser mayor que cero minutos."
    )


def test_validate_new_appointment_same_professional_overlap_is_rejected_with_conflicting_id() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(
        _request(_at(13, 15), chair_id=S2), _refs(service=service, chair=Chair(S2, active=True)), [_appt_a()], CTX
    )

    assert _summary(result) == [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)]
    assert isinstance(result, Rejected)
    assert str(APPT_A) in result.violations[0].message


def _validate(
    request: NewAppointmentRequest,
    existing: list[Appointment],
    default_min: int = 30,
) -> object:
    return validate_new_appointment(
        request,
        _refs(
            professional=Professional(request.professional_id, active=True),
            chair=Chair(request.chair_id, active=True),
            service=Service(id=SVC_30, default_duration_min=default_min),
        ),
        existing, CTX,
    )


@pytest.mark.parametrize(
    ("existing_end", "start", "duration"),
    [
        pytest.param((13, 30), _at(12, 45), 30, id="fin-dentro-de-existente"),
        pytest.param((13, 30), _at(12, 45), 60, id="contiene-al-existente"),
        pytest.param((13, 30), _at(13, 0), 30, id="mismo-intervalo"),
        pytest.param((14, 0), _at(13, 15), 15, id="contenido-en-existente"),
    ],
)
def test_validate_new_appointment_professional_overlap_geometry_is_rejected(
    existing_end: tuple[int, int], start: datetime, duration: int
) -> None:
    existing = [_existing(APPT_A, P1, S1, _at(13), _at(*existing_end))]

    result = _validate(_request(start, chair_id=S2, duration_min=duration), existing)

    assert _summary(result) == [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)]


@pytest.mark.parametrize(
    ("professional_id", "chair_id", "start"),
    [
        pytest.param(P1, S1, _at(13, 30), id="empieza-cuando-termina-otro"),
        pytest.param(P1, S1, _at(12, 30), id="termina-cuando-empieza-otro"),
        pytest.param(P2, S2, _at(13), id="otro-profesional-y-otro-sillon"),
        pytest.param(P1, S1, _at(15), id="otros-turnos-que-no-chocan"),
    ],
)
def test_validate_new_appointment_without_conflict_returns_ok(
    professional_id: UUID, chair_id: UUID, start: datetime
) -> None:
    result = _validate(
        _request(start, professional_id=professional_id, chair_id=chair_id), [_appt_a()]
    )

    assert isinstance(result, Ok)
    assert result.appointment.start_at == start
    assert result.appointment.end_at == start + timedelta(minutes=30)


def test_validate_new_appointment_cancelled_appointment_does_not_block() -> None:
    existing = [_existing(APPT_A, P1, S2, _at(13), _at(13, 30), AppointmentStatus.CANCELLED)]

    result = _validate(_request(_at(13)), existing)

    assert isinstance(result, Ok)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        pytest.param(AppointmentStatus.NO_SHOW, [], id="ausente"),
        pytest.param(
            AppointmentStatus.RESERVED, [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)], id="reservado"
        ),
        pytest.param(
            AppointmentStatus.CONFIRMED,
            [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)],
            id="confirmado",
        ),
        pytest.param(
            AppointmentStatus.ATTENDED, [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)], id="atendido"
        ),
    ],
)
def test_validate_new_appointment_only_occupying_statuses_block_professional(
    status: AppointmentStatus, expected: list[tuple[ViolationCode, UUID]]
) -> None:
    existing = [_existing(APPT_A, P1, S2, _at(13), _at(13, 30), status)]

    result = _validate(_request(_at(13)), existing)

    if expected:
        assert _summary(result) == expected
    else:
        assert isinstance(result, Ok)


def test_validate_new_appointment_invalid_duration_in_busy_slot_reports_only_duration() -> None:
    result = _validate(_request(_at(13), duration_min=0), [_appt_a()])

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_same_chair_other_professional_is_chair_overlap() -> None:
    result = _validate(
        _request(_at(13, 15), professional_id=P2, chair_id=S1, duration_min=30), [_appt_a()]
    )

    assert _summary(result) == [(ViolationCode.CHAIR_OVERLAP, APPT_A)]


def test_validate_new_appointment_same_professional_and_chair_reports_both_in_order() -> None:
    result = _validate(_request(_at(13, 15), duration_min=30), [_appt_a()])

    assert _summary(result) == [
        (ViolationCode.PROFESSIONAL_OVERLAP, APPT_A),
        (ViolationCode.CHAIR_OVERLAP, APPT_A),
    ]


def test_validate_new_appointment_other_chair_same_time_is_ok() -> None:
    result = _validate(_request(_at(13), professional_id=P2, chair_id=S2), [_appt_a()])

    assert isinstance(result, Ok)


@pytest.mark.parametrize(
    "status", [AppointmentStatus.CONFIRMED, AppointmentStatus.ATTENDED]
)
def test_validate_new_appointment_confirmed_and_attended_block_professional_and_chair(
    status: AppointmentStatus,
) -> None:
    existing = [_existing(APPT_A, P1, S1, _at(13), _at(13, 30), status)]

    result = _validate(_request(_at(13)), existing)

    assert _summary(result) == [
        (ViolationCode.PROFESSIONAL_OVERLAP, APPT_A),
        (ViolationCode.CHAIR_OVERLAP, APPT_A),
    ]


def test_validate_new_appointment_no_show_appointment_does_not_block_chair() -> None:
    existing = [_existing(APPT_A, P1, S1, _at(13), _at(13, 30), AppointmentStatus.NO_SHOW)]

    assert isinstance(_validate(_request(_at(13)), existing), Ok)


def test_validate_new_appointment_irrelevant_appointments_in_list_are_ignored() -> None:
    existing = [
        _existing(APPT_B, P2, S2, _at(13), _at(13, 30)),
        _existing(APPT_C, P2, S2, _at(12, 45), _at(13, 15)),
        _existing(APPT_D, P1, S1, _at(13), _at(13, 30), AppointmentStatus.CANCELLED),
    ]

    assert isinstance(_validate(_request(_at(13)), existing), Ok)


def _b() -> Appointment:
    return _existing(APPT_B, P1, S2, _at(13, 30), _at(14))


def _c() -> Appointment:
    return _existing(APPT_C, P1, S3, _at(13), _at(13, 30))


def _d() -> Appointment:
    return _existing(APPT_D, P2, S1, _at(13, 45), _at(14, 15))


EXPECTED_BCD_ORDER = [
    (ViolationCode.PROFESSIONAL_OVERLAP, APPT_C),
    (ViolationCode.PROFESSIONAL_OVERLAP, APPT_B),
    (ViolationCode.CHAIR_OVERLAP, APPT_D),
]


def test_validate_new_appointment_many_conflicts_are_ordered_professional_first_by_start() -> None:
    result = _validate(_request(_at(13), duration_min=60), [_b(), _c(), _d()])

    assert _summary(result) == EXPECTED_BCD_ORDER


@pytest.mark.parametrize(
    "order",
    [
        pytest.param([_d, _c, _b], id="d-c-b"),
        pytest.param([_c, _d, _b], id="c-d-b"),
    ],
)
def test_validate_new_appointment_violation_order_ignores_input_list_order(
    order: list[Callable[[], Appointment]],
) -> None:
    result = _validate(_request(_at(13), duration_min=60), [make() for make in order])

    assert _summary(result) == EXPECTED_BCD_ORDER


def test_validate_new_appointment_same_start_conflicts_are_ordered_by_id() -> None:
    first = _existing(APPT_B, P1, S2, _at(13), _at(13, 30))
    second = _existing(APPT_C, P1, S3, _at(13), _at(13, 30))
    expected = [
        (ViolationCode.PROFESSIONAL_OVERLAP, APPT_B),
        (ViolationCode.PROFESSIONAL_OVERLAP, APPT_C),
    ]

    forward = _validate(_request(_at(13), chair_id=S1), [first, second])
    backward = _validate(_request(_at(13), chair_id=S1), [second, first])

    assert _summary(forward) == expected
    assert _summary(backward) == expected


def test_validate_new_appointment_overlap_messages_name_resource_and_conflicting_id() -> None:
    result = _validate(_request(_at(13, 15), duration_min=30), [_appt_a()])

    assert isinstance(result, Rejected)
    professional_violation, chair_violation = result.violations
    assert str(APPT_A) in professional_violation.message
    assert "profesional" in professional_violation.message
    assert str(APPT_A) in chair_violation.message
    assert "sillón" in chair_violation.message


def test_validate_new_appointment_existing_appointment_in_other_timezone_still_conflicts() -> None:
    buenos_aires = timezone(timedelta(hours=-3))
    existing = [
        _existing(
            APPT_A,
            P1,
            S1,
            datetime(2026, 10, 20, 10, 0, tzinfo=buenos_aires),
            datetime(2026, 10, 20, 10, 30, tzinfo=buenos_aires),
        )
    ]

    result = _validate(_request(_at(13, 15), chair_id=S2, duration_min=30), existing)

    assert _summary(result) == [(ViolationCode.PROFESSIONAL_OVERLAP, APPT_A)]


OTHER_ID = UUID("00000000-0000-0000-0000-0000000000e9")


@pytest.mark.parametrize(
    ("references", "field"),
    [
        pytest.param(_refs(patient=Patient(OTHER_ID)), "patient", id="paciente"),
        pytest.param(
            _refs(professional=Professional(OTHER_ID, active=True)), "professional", id="profesional"
        ),
        pytest.param(_refs(chair=Chair(OTHER_ID, active=True)), "chair", id="sillon"),
        pytest.param(_refs(service=Service(OTHER_ID, 30)), "service", id="prestacion"),
    ],
)
def test_validate_new_appointment_reference_with_other_id_raises_value_error_naming_field(
    references: AppointmentReferences, field: str
) -> None:
    with pytest.raises(ValueError, match=field):
        validate_new_appointment(_request(_at(13)), references, [], CTX)


def test_validate_new_appointment_all_references_none_is_not_a_value_error() -> None:
    references = _refs(patient=None, professional=None, chair=None, service=None)

    result = validate_new_appointment(_request(_at(13), duration_min=0), references, [], CTX)

    assert isinstance(result, Rejected)


def _kinds(result: object) -> list[tuple[ViolationCode, ReferenceKind | None]]:
    assert isinstance(result, Rejected)
    return [(v.code, v.reference_kind) for v in result.violations]


def test_validate_new_appointment_unknown_professional_is_rejected_as_unknown_reference() -> None:
    result = validate_new_appointment(_request(_at(13)), _refs(professional=None), [], CTX)

    assert _kinds(result) == [(ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.PROFESSIONAL)]


@pytest.mark.parametrize(
    ("references", "kind"),
    [
        pytest.param(_refs(patient=None), ReferenceKind.PATIENT, id="paciente"),
        pytest.param(_refs(professional=None), ReferenceKind.PROFESSIONAL, id="profesional"),
        pytest.param(_refs(chair=None), ReferenceKind.CHAIR, id="sillon"),
        pytest.param(_refs(service=None), ReferenceKind.SERVICE, id="prestacion"),
    ],
)
def test_validate_new_appointment_unknown_reference_reports_matching_kind(
    references: AppointmentReferences, kind: ReferenceKind
) -> None:
    result = validate_new_appointment(_request(_at(13), duration_min=30), references, [], CTX)

    assert _kinds(result) == [(ViolationCode.UNKNOWN_REFERENCE, kind)]


def test_validate_new_appointment_unknown_service_without_explicit_duration_skips_duration() -> (
    None
):
    result = validate_new_appointment(_request(_at(13)), _refs(service=None), [], CTX)

    assert _kinds(result) == [(ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.SERVICE)]


@pytest.mark.parametrize(
    ("references", "kind"),
    [
        pytest.param(
            _refs(professional=Professional(P1, active=False)),
            ReferenceKind.PROFESSIONAL,
            id="profesional",
        ),
        pytest.param(_refs(chair=Chair(S1, active=False)), ReferenceKind.CHAIR, id="sillon"),
        pytest.param(
            _refs(service=Service(SVC_30, 30, active=False)), ReferenceKind.SERVICE, id="prestacion"
        ),
    ],
)
def test_validate_new_appointment_inactive_reference_reports_matching_kind(
    references: AppointmentReferences, kind: ReferenceKind
) -> None:
    result = validate_new_appointment(_request(_at(13)), references, [], CTX)

    assert _kinds(result) == [(ViolationCode.INACTIVE_REFERENCE, kind)]


def test_validate_new_appointment_several_failing_references_are_reported_in_fixed_order() -> None:
    references = _refs(
        patient=None,
        professional=Professional(P1, active=False),
        chair=None,
        service=Service(SVC_30, 30, active=False),
    )

    result = validate_new_appointment(_request(_at(13), duration_min=30), references, [], CTX)

    assert _kinds(result) == [
        (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.PATIENT),
        (ViolationCode.INACTIVE_REFERENCE, ReferenceKind.PROFESSIONAL),
        (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.CHAIR),
        (ViolationCode.INACTIVE_REFERENCE, ReferenceKind.SERVICE),
    ]


def test_validate_new_appointment_reference_violation_in_busy_slot_reports_no_overlap() -> None:
    result = validate_new_appointment(
        _request(_at(13)), _refs(chair=Chair(S1, active=False)), [_appt_a()], CTX
    )

    assert _kinds(result) == [(ViolationCode.INACTIVE_REFERENCE, ReferenceKind.CHAIR)]


@pytest.mark.parametrize(
    ("references", "code", "kind", "expected_id"),
    [
        pytest.param(
            _refs(chair=None),
            ViolationCode.UNKNOWN_REFERENCE,
            ReferenceKind.CHAIR,
            S1,
            id="sillon-inexistente",
        ),
        pytest.param(
            _refs(professional=Professional(P1, active=False)),
            ViolationCode.INACTIVE_REFERENCE,
            ReferenceKind.PROFESSIONAL,
            P1,
            id="profesional-inactivo",
        ),
    ],
)
def test_validate_new_appointment_reference_violation_has_kind_id_in_message_and_no_conflict(
    references: AppointmentReferences, code: ViolationCode, kind: ReferenceKind, expected_id: UUID
) -> None:
    result = validate_new_appointment(_request(_at(13)), references, [], CTX)

    assert isinstance(result, Rejected)
    (violation,) = result.violations
    assert (violation.code, violation.reference_kind) == (code, kind)
    assert str(expected_id) in violation.message
    assert violation.conflicting_appointment_id is None


@pytest.mark.parametrize("explicit_min", [7, 32])
def test_validate_new_appointment_duration_not_multiple_of_five_is_invalid_duration(
    explicit_min: int,
) -> None:
    result = validate_new_appointment(_request(_at(13), duration_min=explicit_min), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_duration_above_maximum_is_invalid_duration() -> None:
    result = validate_new_appointment(_request(_at(13), duration_min=490), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


@pytest.mark.parametrize(
    ("start", "explicit_min", "default_min", "expected_end"),
    [
        pytest.param(_at(8), 480, 30, _at(16), id="maxima"),
        pytest.param(_at(13), 5, 30, _at(13, 5), id="minima"),
        pytest.param(_at(13), 30, 485, _at(13, 30), id="explicita-reemplaza-defecto-invalido"),
    ],
)
def test_validate_new_appointment_valid_duration_boundaries_return_ok(
    start: datetime, explicit_min: int, default_min: int, expected_end: datetime
) -> None:
    result = validate_new_appointment(
        _request(start, duration_min=explicit_min),
        _refs(service=Service(SVC_30, default_min)),
        [], CTX,
    )

    assert isinstance(result, Ok)
    assert (result.appointment.start_at, result.appointment.end_at) == (start, expected_end)


def test_validate_new_appointment_default_duration_not_multiple_of_five_is_rejected() -> None:
    result = validate_new_appointment(
        _request(_at(13)), _refs(service=Service(SVC_30, 32)), [], CTX
    )

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]



def test_validate_new_appointment_duration_breaking_two_conditions_gives_one_violation() -> None:
    result = validate_new_appointment(_request(_at(13), duration_min=487), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_duration_breaking_two_conditions_message_names_all_reasons() -> (
    None
):
    result = validate_new_appointment(_request(_at(13), duration_min=487), _refs(), [], CTX)

    assert isinstance(result, Rejected)
    message = result.violations[0].message
    assert "487" in message
    assert "múltiplo de 5" in message
    assert "480" in message


def test_validate_new_appointment_invalid_reference_and_duration_are_reported_together() -> None:
    result = validate_new_appointment(
        _request(_at(13), duration_min=7), _refs(professional=None), [], CTX
    )

    assert _kinds(result) == [
        (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.PROFESSIONAL),
        (ViolationCode.INVALID_DURATION, None),
    ]


@pytest.mark.parametrize(
    ("references", "explicit_min", "expected"),
    [
        pytest.param(
            _refs(service=None),
            7,
            [
                (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.SERVICE),
                (ViolationCode.INVALID_DURATION, None),
            ],
            id="prestacion-inexistente-con-explicita-invalida",
        ),
        pytest.param(
            _refs(service=Service(SVC_30, 485, active=False)),
            None,
            [
                (ViolationCode.INACTIVE_REFERENCE, ReferenceKind.SERVICE),
                (ViolationCode.INVALID_DURATION, None),
            ],
            id="prestacion-inactiva-con-defecto-invalido",
        ),
    ],
)
def test_validate_new_appointment_service_problem_and_invalid_duration_are_reported_in_order(
    references: AppointmentReferences,
    explicit_min: int | None,
    expected: list[tuple[ViolationCode, ReferenceKind | None]],
) -> None:
    result = validate_new_appointment(
        _request(_at(13), duration_min=explicit_min), references, [], CTX
    )

    assert _kinds(result) == expected


@pytest.mark.parametrize(
    ("duration_min", "expected"),
    [
        pytest.param(
            30,
            [
                (ViolationCode.PROFESSIONAL_OVERLAP, None),
                (ViolationCode.CHAIR_OVERLAP, None),
            ],
            id="solapamientos",
        ),
        pytest.param(7, [(ViolationCode.INVALID_DURATION, None)], id="duracion-invalida"),
    ],
)
def test_validate_new_appointment_non_reference_violations_have_no_reference_kind(
    duration_min: int, expected: list[tuple[ViolationCode, ReferenceKind | None]]
) -> None:
    result = validate_new_appointment(
        _request(_at(13, 15), duration_min=duration_min), _refs(), [_appt_a()], CTX
    )

    assert _kinds(result) == expected


def test_validate_new_appointment_start_on_grid_returns_ok() -> None:
    result = validate_new_appointment(_request(_local(20, 10, 5)), _refs(), [], CTX)

    assert result == Ok(
        Appointment(
            id=T_NEW,
            patient_id=PATIENT,
            professional_id=P1,
            chair_id=S1,
            service_id=SVC_30,
            start_at=datetime.fromisoformat("2026-10-20T13:05:00+00:00"),
            end_at=datetime.fromisoformat("2026-10-20T13:35:00+00:00"),
            status=AppointmentStatus.RESERVED,
        )
    )


def test_validate_new_appointment_start_minutes_off_grid_is_rejected_as_invalid_start_time() -> None:
    result = validate_new_appointment(_request(_local(20, 10, 3)), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_START_TIME, None)]


@pytest.mark.parametrize(
    ("start", "shown_time"),
    [
        pytest.param(_local(20, 10, 5, 30), "10:05:30", id="segundos"),
        pytest.param(_local(20, 10, 5, 0, 250000), "10:05:00", id="microsegundos"),
    ],
)
def test_validate_new_appointment_start_with_seconds_or_microseconds_is_rejected_with_time_shown(
    start: datetime, shown_time: str
) -> None:
    result = validate_new_appointment(_request(start), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_START_TIME, None)]
    assert isinstance(result, Rejected)
    assert shown_time in result.violations[0].message


def test_validate_new_appointment_start_breaking_two_conditions_gives_one_violation_with_exact_message() -> (
    None
):
    result = validate_new_appointment(_request(_local(20, 10, 3, 30)), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_START_TIME, None)]
    assert isinstance(result, Rejected)
    assert result.violations[0].message == (
        "El inicio del turno no es válido (se recibió 10:03:30, hora local): "
        "debe caer en un minuto múltiplo de 5 y no puede tener segundos ni fracciones de segundo."
    )


def test_validate_new_appointment_start_off_grid_message_names_time_and_reason() -> None:
    result = validate_new_appointment(_request(_local(20, 10, 3)), _refs(), [], CTX)

    assert isinstance(result, Rejected)
    violation = result.violations[0]
    assert "10:03, hora local" in violation.message
    assert "debe caer en un minuto múltiplo de 5" in violation.message
    assert "segundos" not in violation.message
    assert violation.conflicting_appointment_id is None
    assert violation.reference_kind is None


@pytest.mark.parametrize(
    "start",
    [
        pytest.param(_local(20, 10, 5, 30), id="segundos"),
        pytest.param(_local(20, 10, 5, 0, 250000), id="microsegundos"),
    ],
)
def test_validate_new_appointment_start_with_seconds_message_names_only_seconds_reason(
    start: datetime,
) -> None:
    result = validate_new_appointment(_request(start), _refs(), [], CTX)

    assert isinstance(result, Rejected)
    message = result.violations[0].message
    assert "no puede tener segundos ni fracciones de segundo" in message
    assert "múltiplo de 5" not in message


def test_validate_new_appointment_unknown_reference_invalid_duration_and_invalid_start_are_reported_together() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(20, 10, 3), duration_min=7), _refs(professional=None), [], CTX
    )

    assert _kinds(result) == [
        (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.PROFESSIONAL),
        (ViolationCode.INVALID_DURATION, None),
        (ViolationCode.INVALID_START_TIME, None),
    ]


def test_validate_new_appointment_start_off_grid_in_busy_slot_reports_only_start() -> None:
    result = validate_new_appointment(_request(_local(20, 10, 3)), _refs(), [_appt_a()], CTX)

    assert _summary(result) == [(ViolationCode.INVALID_START_TIME, None)]


def test_validate_new_appointment_crossing_local_midnight_is_rejected_as_crosses_midnight() -> None:
    result = validate_new_appointment(
        _request(_local(20, 23, 30), duration_min=60), _refs(), [], CTX
    )

    assert _summary(result) == [(ViolationCode.CROSSES_MIDNIGHT, None)]


@pytest.mark.parametrize(
    ("start", "duration", "expected_start", "expected_end"),
    [
        pytest.param(
            _local(20, 23, 0),
            55,
            "2026-10-21T02:00:00+00:00",
            "2026-10-21T02:55:00+00:00",
            id="termina-antes-de-la-medianoche",
        ),
        pytest.param(
            _local(20, 23, 30),
            None,
            "2026-10-21T02:30:00+00:00",
            "2026-10-21T03:00:00+00:00",
            id="termina-justo-a-la-medianoche",
        ),
    ],
)
def test_validate_new_appointment_ending_at_or_before_local_midnight_returns_ok(
    start: datetime, duration: int | None, expected_start: str, expected_end: str
) -> None:
    result = validate_new_appointment(_request(start, duration_min=duration), _refs(), [], CTX)

    assert isinstance(result, Ok)
    assert result.appointment.start_at == datetime.fromisoformat(expected_start)
    assert result.appointment.end_at == datetime.fromisoformat(expected_end)


def test_validate_new_appointment_utc_instant_on_previous_local_day_is_rejected_as_crosses_midnight() -> (
    None
):
    start = datetime.fromisoformat("2026-10-20T02:30:00+00:00")

    result = validate_new_appointment(_request(start, duration_min=60), _refs(), [], CTX)

    assert _summary(result) == [(ViolationCode.CROSSES_MIDNIGHT, None)]


def test_validate_new_appointment_crossing_utc_midnight_but_not_local_midnight_returns_ok() -> None:
    start = datetime.fromisoformat("2026-10-20T23:30:00+00:00")

    result = validate_new_appointment(_request(start, duration_min=60), _refs(), [], CTX)

    assert isinstance(result, Ok)
    assert result.appointment.end_at == datetime.fromisoformat("2026-10-21T00:30:00+00:00")


def test_validate_new_appointment_invalid_duration_crossing_midnight_reports_only_duration() -> None:
    result = validate_new_appointment(
        _request(_local(20, 23, 30), duration_min=62), _refs(), [], CTX
    )

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_off_grid_start_crossing_midnight_reports_start_then_midnight() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(20, 23, 33), duration_min=60), _refs(), [], CTX
    )

    assert _summary(result) == [
        (ViolationCode.INVALID_START_TIME, None),
        (ViolationCode.CROSSES_MIDNIGHT, None),
    ]


def test_validate_new_appointment_crosses_midnight_message_shows_local_start_and_end() -> None:
    result = validate_new_appointment(
        _request(_local(20, 23, 30), duration_min=60), _refs(), [], CTX
    )

    assert isinstance(result, Rejected)
    violation = result.violations[0]
    assert "23:30" in violation.message
    assert "00:30" in violation.message
    assert "02:30" not in violation.message
    assert violation.conflicting_appointment_id is None
    assert violation.reference_kind is None


def test_validate_new_appointment_off_grid_start_with_seconds_crossing_midnight_by_seconds_reports_both() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(20, 23, 30, 30), duration_min=30), _refs(), [], CTX
    )

    assert _summary(result) == [
        (ViolationCode.INVALID_START_TIME, None),
        (ViolationCode.CROSSES_MIDNIGHT, None),
    ]


def test_validate_new_appointment_starting_inside_and_ending_after_the_slot_is_outside_working_hours() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(20, 12, 30), duration_min=60), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def _start_and_end_iso(result: object) -> tuple[str, str]:
    assert isinstance(result, Ok)
    return result.appointment.start_at.isoformat(), result.appointment.end_at.isoformat()


@pytest.mark.parametrize(
    ("start_at", "duration_min", "expected_start_iso", "expected_end_iso"),
    [
        (_local(20, 10, 0), 30, "2026-10-20T13:00:00+00:00", "2026-10-20T13:30:00+00:00"),
        (_local(20, 9, 0), 30, "2026-10-20T12:00:00+00:00", "2026-10-20T12:30:00+00:00"),
        (_local(20, 12, 30), 30, "2026-10-20T15:30:00+00:00", "2026-10-20T16:00:00+00:00"),
        (_local(20, 18, 30), 30, "2026-10-20T21:30:00+00:00", "2026-10-20T22:00:00+00:00"),
    ],
    ids=["completo-dentro", "justo-al-inicio", "justo-al-fin-de-la-manana", "justo-al-fin-de-la-tarde"],
)
def test_validate_new_appointment_inside_a_slot_returns_ok(
    start_at: datetime, duration_min: int, expected_start_iso: str, expected_end_iso: str
) -> None:
    result = validate_new_appointment(
        _request(start_at, duration_min=duration_min), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _start_and_end_iso(result) == (expected_start_iso, expected_end_iso)


@pytest.mark.parametrize(
    ("start_at", "duration_min"),
    [
        (_local(20, 8, 30), 60),
        (_local(20, 13, 0), 120),
        (_local(20, 14, 0), 30),
        (_local(20, 12, 30), 180),
        (_local(25, 10, 0), 30),
    ],
    ids=["empieza-antes", "ocupa-el-hueco", "dentro-del-hueco", "une-tramos-con-hueco", "domingo"],
)
def test_validate_new_appointment_outside_the_slots_is_rejected(
    start_at: datetime, duration_min: int
) -> None:
    result = validate_new_appointment(
        _request(start_at, duration_min=duration_min), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def test_validate_new_appointment_utc_instant_inside_slot_but_outside_in_local_time_is_rejected() -> (
    None
):
    start_at = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)  # 06:00 hora local

    result = validate_new_appointment(
        _request(start_at, duration_min=30), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def test_validate_new_appointment_utc_instant_outside_slots_but_inside_in_local_time_returns_ok() -> (
    None
):
    start_at = datetime(2026, 10, 20, 21, 0, tzinfo=timezone.utc)  # 18:00 hora local

    result = validate_new_appointment(
        _request(start_at, duration_min=30), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _start_and_end_iso(result) == ("2026-10-20T21:00:00+00:00", "2026-10-20T21:30:00+00:00")


def test_validate_new_appointment_weekday_is_the_local_one_not_the_utc_one() -> None:
    wednesday_only = _ctx(WorkingHours(P1, 3, 1200, 1380))

    result = validate_new_appointment(
        _request(_local(20, 22, 0), duration_min=30), _refs(), [], wednesday_only
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def test_validate_new_appointment_tuesday_local_evening_that_is_wednesday_in_utc_returns_ok() -> None:
    tuesday_only = _ctx(WorkingHours(P1, 2, 1200, 1380))

    result = validate_new_appointment(
        _request(_local(20, 22, 0), duration_min=30), _refs(), [], tuesday_only
    )

    assert _start_and_end_iso(result) == ("2026-10-21T01:00:00+00:00", "2026-10-21T01:30:00+00:00")


def test_validate_new_appointment_ending_at_local_midnight_at_slot_end_returns_ok() -> None:
    until_midnight = _ctx(WorkingHours(P1, 2, 1200, 1440))

    result = validate_new_appointment(
        _request(_local(20, 23, 30), duration_min=30), _refs(), [], until_midnight
    )

    assert _start_and_end_iso(result) == ("2026-10-21T02:30:00+00:00", "2026-10-21T03:00:00+00:00")


def test_validate_new_appointment_slot_of_another_professional_does_not_count() -> None:
    result = validate_new_appointment(
        _request(_local(20, 10, 0), duration_min=30), _refs(), [], _ctx(WorkingHours(P2, 2, 540, 780))
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def test_validate_new_appointment_ending_at_local_midnight_after_slot_end_is_rejected() -> None:
    until_23 = _ctx(WorkingHours(P1, 2, 1200, 1380))

    result = validate_new_appointment(
        _request(_local(20, 23, 30), duration_min=30), _refs(), [], until_23
    )

    assert _summary(result) == [(ViolationCode.OUTSIDE_WORKING_HOURS, None)]


def test_validate_new_appointment_spanning_two_contiguous_slots_returns_ok() -> None:
    contiguous = _ctx(WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 780, 1020))

    result = validate_new_appointment(
        _request(_local(20, 12, 30), duration_min=60), _refs(), [], contiguous
    )

    assert _start_and_end_iso(result) == ("2026-10-20T15:30:00+00:00", "2026-10-20T16:30:00+00:00")


def test_validate_new_appointment_slot_nested_in_another_does_not_shorten_the_merged_slot() -> None:
    nested = _ctx(WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 600, 700))

    result = validate_new_appointment(
        _request(_local(20, 12, 0), duration_min=30), _refs(), [], nested
    )

    assert _start_and_end_iso(result) == ("2026-10-20T15:00:00+00:00", "2026-10-20T15:30:00+00:00")


def _only_violation_of(result: object) -> Violation:
    assert isinstance(result, Rejected)
    assert len(result.violations) == 1
    return result.violations[0]


def test_validate_new_appointment_outside_working_hours_message_lists_the_day_slots() -> None:
    result = validate_new_appointment(
        _request(_local(20, 12, 30), duration_min=60), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    violation = _only_violation_of(result)
    assert violation.message == (
        "El turno de 12:30 a 13:30 (hora local) queda fuera del horario de atención del "
        "profesional: el martes atiende de 09:00 a 13:00 y de 15:00 a 19:00."
    )
    assert violation.conflicting_appointment_id is None
    assert violation.reference_kind is None


def test_validate_new_appointment_outside_working_hours_message_on_a_day_without_slots() -> None:
    result = validate_new_appointment(
        _request(_local(25, 10, 0), duration_min=30), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _only_violation_of(result).message == (
        "El turno de 10:00 a 10:30 (hora local) queda fuera del horario de atención del "
        "profesional: no atiende los domingos."
    )


def test_validate_new_appointment_outside_working_hours_message_merges_slots_and_shows_24() -> None:
    unordered = _ctx(
        WorkingHours(P1, 2, 1200, 1440), WorkingHours(P1, 2, 780, 1020), WorkingHours(P1, 2, 540, 780)
    )

    result = validate_new_appointment(
        _request(_local(20, 17, 30), duration_min=30), _refs(), [], unordered
    )

    assert _only_violation_of(result).message == (
        "El turno de 17:30 a 18:00 (hora local) queda fuera del horario de atención del "
        "profesional: el martes atiende de 09:00 a 17:00 y de 20:00 a 24:00."
    )


def test_validate_new_appointment_outside_working_hours_and_overlapping_reports_horario_first() -> (
    None
):
    existing_b = _existing(APPT_B, P1, S1, _local(20, 12, 30), _local(20, 13, 30))

    result = validate_new_appointment(
        _request(_local(20, 12, 45), duration_min=30), _refs(), [existing_b], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [
        (ViolationCode.OUTSIDE_WORKING_HOURS, None),
        (ViolationCode.PROFESSIONAL_OVERLAP, APPT_B),
        (ViolationCode.CHAIR_OVERLAP, APPT_B),
    ]


def test_validate_new_appointment_invalid_duration_on_a_day_without_slots_reports_only_duration() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(25, 10, 0), duration_min=7), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_off_grid_start_on_a_day_without_slots_reports_only_start() -> (
    None
):
    result = validate_new_appointment(
        _request(_local(25, 10, 3), duration_min=30), _refs(), [], _ctx(*TUESDAY_BASE)
    )

    assert _summary(result) == [(ViolationCode.INVALID_START_TIME, None)]


# --- Bloqueos (C-06) ---


def _block(
    id: UUID,
    start_at: datetime,
    end_at: datetime,
    *,
    professional_id: UUID = P1,
    reason: str | None = None,
) -> Block:
    return Block(
        id=id, professional_id=professional_id, start_at=start_at, end_at=end_at, reason=reason
    )


def _bl1(reason: str | None = None) -> Block:
    # P1, martes 2026-10-20 de 10:00 a 12:00 hora local = 13:00 a 15:00 UTC
    return _block(BL1, _local(20, 10, 0), _local(20, 12, 0), reason=reason)


def _ctx_now(
    now: datetime, working_hours: tuple[WorkingHours, ...] = FULL_WEEK
) -> ScheduleContext:
    return ScheduleContext(tz=BUENOS_AIRES, working_hours=working_hours, blocks=(), now=now)


def _ctx_blocks(
    *blocks: Block, working_hours: tuple[WorkingHours, ...] = FULL_WEEK
) -> ScheduleContext:
    return ScheduleContext(
        tz=BUENOS_AIRES, working_hours=working_hours, blocks=blocks, now=EARLY_NOW
    )


def _block_summary(result: object) -> list[tuple[ViolationCode, UUID | None]]:
    assert isinstance(result, Rejected)
    return [(v.code, v.conflicting_block_id) for v in result.violations]


def test_validate_new_appointment_inside_a_block_reports_blocked_time_with_block_id() -> None:
    # 10:30 a 11:00 hora local = 13:30 a 14:00 UTC
    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=30), _refs(), [], _ctx_blocks(_bl1())
    )

    assert _block_summary(result) == [(ViolationCode.BLOCKED_TIME, BL1)]


@pytest.mark.parametrize(
    ("start_local", "expected"),
    [
        # 09:30 a 10:00 hora local = 12:30 a 13:00 UTC: termina cuando empieza BL1
        (_local(20, 9, 30), []),
        # 12:00 a 12:30 hora local = 15:00 a 15:30 UTC: empieza cuando termina BL1
        (_local(20, 12, 0), []),
        # 09:45 a 10:15 hora local = 12:45 a 13:15 UTC: pisa el inicio de BL1
        (_local(20, 9, 45), [(ViolationCode.BLOCKED_TIME, BL1)]),
        # 11:45 a 12:15 hora local = 14:45 a 15:15 UTC: pisa el fin de BL1
        (_local(20, 11, 45), [(ViolationCode.BLOCKED_TIME, BL1)]),
    ],
    ids=["termina-al-inicio", "empieza-al-fin", "pisa-el-inicio", "pisa-el-fin"],
)
def test_validate_new_appointment_block_edges_are_half_open(
    start_local: datetime, expected: list[tuple[ViolationCode, UUID | None]]
) -> None:
    result = validate_new_appointment(
        _request(start_local, duration_min=30), _refs(), [], _ctx_blocks(_bl1())
    )

    if expected:
        assert _block_summary(result) == expected
    else:
        assert isinstance(result, Ok)


def test_validate_new_appointment_block_of_another_professional_does_not_count() -> None:
    # Bloqueo de P2 de 10:00 a 12:00 hora local = 13:00 a 15:00 UTC; pedido de P1 de 10:30 a 11:00
    p2_block = _block(BL1, _local(20, 10, 0), _local(20, 12, 0), professional_id=P2)

    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=30), _refs(), [], _ctx_blocks(p2_block)
    )

    assert isinstance(result, Ok)


def _blv(reason: str | None = "vacaciones") -> Block:
    # Lunes 2026-10-19 00:00 a lunes 2026-10-26 00:00 hora local = 03:00 UTC del 19 a 03:00 UTC del 26
    return _block(BLV, _local(19, 0, 0), _local(26, 0, 0), reason=reason)


@pytest.mark.parametrize(
    ("start_utc", "duration_min", "expected"),
    [
        # martes 20 de 10:00 a 10:30 hora local
        (datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc), 30, [(ViolationCode.BLOCKED_TIME, BLV)]),
        # domingo 25 de 23:30 a 23:55 hora local: en UTC ya es el 26, pero antes de las 03:00
        (datetime(2026, 10, 26, 2, 30, tzinfo=timezone.utc), 25, [(ViolationCode.BLOCKED_TIME, BLV)]),
        # lunes 26 de 00:00 a 00:30 hora local: empieza cuando termina BLV
        (datetime(2026, 10, 26, 3, 0, tzinfo=timezone.utc), 30, []),
        # domingo 18 de 23:30 a 00:00 hora local: termina cuando empieza BLV
        (datetime(2026, 10, 19, 2, 30, tzinfo=timezone.utc), 30, []),
    ],
    ids=["martes-dentro", "ultimo-turno-del-domingo-local", "empieza-al-fin", "termina-al-inicio"],
)
def test_validate_new_appointment_multi_day_block_compares_instants(
    start_utc: datetime, duration_min: int, expected: list[tuple[ViolationCode, UUID | None]]
) -> None:
    result = validate_new_appointment(
        _request(start_utc, duration_min=duration_min), _refs(), [], _ctx_blocks(_blv())
    )

    if expected:
        assert _block_summary(result) == expected
    else:
        assert isinstance(result, Ok)


def _bl2() -> Block:
    # P1, martes 2026-10-20 de 11:00 a 13:00 hora local = 14:00 a 16:00 UTC
    return _block(BL2, _local(20, 11, 0), _local(20, 13, 0))


@pytest.mark.parametrize(
    "blocks",
    [(_bl1(), _bl2()), (_bl2(), _bl1())],
    ids=["en-orden", "invertidos"],
)
def test_validate_new_appointment_overlapping_two_blocks_reports_both_in_start_order(
    blocks: tuple[Block, ...],
) -> None:
    # 11:30 a 12:30 hora local = 14:30 a 15:30 UTC
    result = validate_new_appointment(
        _request(_local(20, 11, 30), duration_min=60), _refs(), [], _ctx_blocks(*blocks)
    )

    assert _block_summary(result) == [
        (ViolationCode.BLOCKED_TIME, BL1),
        (ViolationCode.BLOCKED_TIME, BL2),
    ]


def test_validate_new_appointment_blocked_time_message_without_reason() -> None:
    # 10:30 a 11:00 hora local = 13:30 a 14:00 UTC
    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=30), _refs(), [], _ctx_blocks(_bl1())
    )

    violation = _only_violation_of(result)
    assert violation.message == (
        f"El turno de 10:30 a 11:00 (hora local) se superpone con el bloqueo {BL1} del "
        "profesional, del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local)."
    )
    assert violation.conflicting_appointment_id is None
    assert violation.reference_kind is None


def test_validate_new_appointment_blocked_time_message_multi_day_block_with_reason() -> None:
    # Domingo 25 de 23:30 a 23:55 hora local = 02:30 a 02:55 UTC del 2026-10-26
    result = validate_new_appointment(
        _request(_local(25, 23, 30), duration_min=25), _refs(), [], _ctx_blocks(_blv())
    )

    message = _only_violation_of(result).message
    assert message == (
        f"El turno de 23:30 a 23:55 (hora local) se superpone con el bloqueo {BLV} del "
        "profesional, del 19/10/2026 00:00 al 26/10/2026 00:00 (hora local). Motivo: vacaciones."
    )
    assert "02:30" not in message
    assert "03:00" not in message


@pytest.mark.parametrize("reason", ["", "   "], ids=["vacio", "solo-espacios"])
def test_validate_new_appointment_blocked_time_message_blank_reason_counts_as_none(
    reason: str,
) -> None:
    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=30), _refs(), [], _ctx_blocks(_bl1(reason))
    )

    assert _only_violation_of(result).message == (
        f"El turno de 10:30 a 11:00 (hora local) se superpone con el bloqueo {BL1} del "
        "profesional, del 20/10/2026 10:00 al 20/10/2026 12:00 (hora local)."
    )


def test_validate_new_appointment_outside_hours_blocked_and_overlapping_reports_all_in_order() -> (
    None
):
    # BL3: P1 de 12:00 a 14:00 hora local = 15:00 a 17:00 UTC
    bl3 = _block(BL3, _local(20, 12, 0), _local(20, 14, 0))
    # E: P1/S2 de 12:30 a 13:00 hora local = 15:30 a 16:00 UTC
    existing_e = _existing(APPT_E, P1, S2, _local(20, 12, 30), _local(20, 13, 0))
    # F: P2/S1 de 12:45 a 13:15 hora local = 15:45 a 16:15 UTC
    existing_f = _existing(APPT_F, P2, S1, _local(20, 12, 45), _local(20, 13, 15))

    # Pedido P1/S1 de 12:30 a 13:30 hora local = 15:30 a 16:30 UTC
    result = validate_new_appointment(
        _request(_local(20, 12, 30), duration_min=60),
        _refs(),
        [existing_f, existing_e],
        _ctx_blocks(bl3, working_hours=TUESDAY_BASE),
    )

    assert isinstance(result, Rejected)
    assert [
        (v.code, v.conflicting_block_id, v.conflicting_appointment_id) for v in result.violations
    ] == [
        (ViolationCode.OUTSIDE_WORKING_HOURS, None, None),
        (ViolationCode.BLOCKED_TIME, BL3, None),
        (ViolationCode.PROFESSIONAL_OVERLAP, None, APPT_E),
        (ViolationCode.CHAIR_OVERLAP, None, APPT_F),
    ]


def test_validate_new_appointment_invalid_duration_inside_a_block_reports_only_duration() -> None:
    # 10:30 hora local = 13:30 UTC, dentro de BL1, con duración explícita de 0 minutos
    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=0), _refs(), [], _ctx_blocks(_bl1())
    )

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_invalid_block_in_context_is_ignored_without_raising() -> None:
    # Bloqueo de P1 de 12:00 a 10:00 hora local (inicio posterior al fin); turno de 10:30 a 11:00
    invalid = _block(BL1, _local(20, 12, 0), _local(20, 10, 0))

    result = validate_new_appointment(
        _request(_local(20, 10, 30), duration_min=30), _refs(), [], _ctx_blocks(invalid)
    )

    assert isinstance(result, Ok)


def test_validate_new_appointment_start_five_minutes_before_now_reports_in_the_past() -> None:
    # now 10:00 hora local = 13:00 UTC; inicio 09:55 hora local = 12:55 UTC
    now = _local(20, 10, 0)

    result = validate_new_appointment(_request(_at(12, 55)), _refs(), [], _ctx_now(now))

    assert _summary(result) == [(ViolationCode.IN_THE_PAST, None)]


# --- C-07: la regla del pasado y su lugar en el grupo 1 (design D1) ---

# martes 2026-10-20, 10:00 hora local = 13:00 UTC
NOW_1000 = datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc)


def _codes(result: object) -> list[ViolationCode]:
    assert isinstance(result, Rejected)
    return [v.code for v in result.violations]


@pytest.mark.parametrize(
    ("now", "start_at"),
    [
        # now 10:00:30 (13:00:30 UTC); inicio 10:00 (13:00 UTC): mismo minuto
        (datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc), _at(13)),
        # now 13:00:00.000001 UTC; inicio 10:00 (13:00 UTC): un microsegundo despues
        (datetime(2026, 10, 20, 13, 0, 0, 1, tzinfo=timezone.utc), _at(13)),
        # now 23:30 hora local = 02:30 UTC del 21; inicio 23:00 = 02:00 UTC del 21
        (
            datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 2, 0, tzinfo=timezone.utc),
        ),
    ],
    ids=["segundos-mismo-minuto", "microsegundo-despues", "mismo-dia-local-otro-dia-utc"],
)
def test_validate_new_appointment_start_before_now_is_rejected_as_in_the_past(
    now: datetime, start_at: datetime
) -> None:
    result = validate_new_appointment(_request(start_at), _refs(), [], _ctx_now(now))

    assert _codes(result) == [ViolationCode.IN_THE_PAST]


def test_validate_new_appointment_off_grid_start_in_the_past_reports_start_then_past() -> None:
    # inicio 09:52 hora local = 12:52 UTC, sin duracion explicita
    result = validate_new_appointment(
        _request(datetime(2026, 10, 20, 12, 52, tzinfo=timezone.utc)), _refs(), [], _ctx_now(NOW_1000)
    )

    assert _codes(result) == [ViolationCode.INVALID_START_TIME, ViolationCode.IN_THE_PAST]


def test_validate_new_appointment_past_crossing_midnight_reports_midnight_then_past() -> None:
    # now 23:45 hora local = 02:45 UTC del 21; inicio 23:30 = 02:30 UTC del 21, 60 min
    now = datetime(2026, 10, 21, 2, 45, tzinfo=timezone.utc)
    start_at = datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc)

    result = validate_new_appointment(
        _request(start_at, duration_min=60), _refs(), [], _ctx_now(now)
    )

    assert _codes(result) == [ViolationCode.CROSSES_MIDNIGHT, ViolationCode.IN_THE_PAST]


def test_validate_new_appointment_invalid_duration_in_the_past_still_reports_past() -> None:
    # 09:00 hora local = 12:00 UTC, 7 minutos
    result = validate_new_appointment(
        _request(_at(12), duration_min=7), _refs(), [], _ctx_now(NOW_1000)
    )

    assert _codes(result) == [ViolationCode.INVALID_DURATION, ViolationCode.IN_THE_PAST]


def test_validate_new_appointment_unknown_service_in_the_past_still_reports_past() -> None:
    # 09:00 hora local = 12:00 UTC, sin prestacion ni duracion explicita
    result = validate_new_appointment(
        _request(_at(12)), _refs(service=None), [], _ctx_now(NOW_1000)
    )

    assert isinstance(result, Rejected)
    assert [(v.code, v.reference_kind) for v in result.violations] == [
        (ViolationCode.UNKNOWN_REFERENCE, ReferenceKind.SERVICE),
        (ViolationCode.IN_THE_PAST, None),
    ]


def test_validate_new_appointment_past_in_an_occupied_slot_reports_only_past() -> None:
    # turno reservado de P1 en S1 de 09:00 a 09:30 hora local = 12:00 a 12:30 UTC
    existing = [_existing(APPT_A, P1, S1, _at(12), _at(12, 30))]

    result = validate_new_appointment(
        _request(_at(12), duration_min=30), _refs(), existing, _ctx_now(NOW_1000)
    )

    assert _codes(result) == [ViolationCode.IN_THE_PAST]


def test_validate_new_appointment_past_outside_working_hours_reports_only_past() -> None:
    # TUESDAY_BASE: P1 atiende desde las 09:00; pedido a las 08:00 hora local = 11:00 UTC
    result = validate_new_appointment(
        _request(_at(11), duration_min=30), _refs(), [], _ctx_now(NOW_1000, TUESDAY_BASE)
    )

    assert _codes(result) == [ViolationCode.IN_THE_PAST]


@pytest.mark.parametrize(
    ("now", "start_at", "expected_message"),
    [
        # now 10:00 hora local (13:00 UTC); inicio 09:55 (12:55 UTC)
        (
            NOW_1000,
            _at(12, 55),
            "El inicio del turno (20/10/2026 09:55, hora local) es anterior al momento "
            "actual (20/10/2026 10:00:00, hora local): no se pueden dar turnos en el pasado.",
        ),
        # now 10:00:30 hora local (13:00:30 UTC); inicio 10:00 (13:00 UTC)
        (
            datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc),
            _at(13),
            "El inicio del turno (20/10/2026 10:00, hora local) es anterior al momento "
            "actual (20/10/2026 10:00:30, hora local): no se pueden dar turnos en el pasado.",
        ),
        # now 23:30 hora local = 02:30 UTC del 21; inicio 23:00 = 02:00 UTC del 21
        (
            datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 2, 0, tzinfo=timezone.utc),
            "El inicio del turno (20/10/2026 23:00, hora local) es anterior al momento "
            "actual (20/10/2026 23:30:00, hora local): no se pueden dar turnos en el pasado.",
        ),
    ],
    ids=["cinco-minutos-antes", "mismo-minuto", "fecha-local-no-utc"],
)
def test_validate_new_appointment_in_the_past_message_is_exact_and_has_no_conflict_ids(
    now: datetime, start_at: datetime, expected_message: str
) -> None:
    result = validate_new_appointment(_request(start_at), _refs(), [], _ctx_now(now))

    violation = _only_violation_of(result)
    assert violation.code == ViolationCode.IN_THE_PAST
    assert violation.message == expected_message
    assert violation.conflicting_appointment_id is None
    assert violation.conflicting_block_id is None
    assert violation.reference_kind is None


@pytest.mark.parametrize(
    ("now", "start_at", "expected_end"),
    [
        # inicio igual al momento actual: 10:00 hora local = 13:00 UTC
        (NOW_1000, _at(13), _at(13, 30)),
        # inicio posterior: 10:05 hora local = 13:05 UTC
        (NOW_1000, _at(13, 5), _at(13, 35)),
        # now 10:00:30 e inicio 10:05 (paso siguiente de la grilla)
        (datetime(2026, 10, 20, 13, 0, 30, tzinfo=timezone.utc), _at(13, 5), _at(13, 35)),
        # now 23:30 hora local (02:30 UTC del 21); inicio 21/10 00:00 hora local = 03:00 UTC
        (
            datetime(2026, 10, 21, 2, 30, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 3, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 3, 30, tzinfo=timezone.utc),
        ),
    ],
    ids=[
        "inicio-igual-al-momento-actual",
        "inicio-posterior",
        "segundos-paso-siguiente",
        "antes-de-medianoche-inicio-dia-siguiente",
    ],
)
def test_validate_new_appointment_start_not_before_now_returns_ok(
    now: datetime, start_at: datetime, expected_end: datetime
) -> None:
    result = validate_new_appointment(_request(start_at), _refs(), [], _ctx_now(now))

    assert isinstance(result, Ok)
    assert result.appointment.start_at == start_at
    assert result.appointment.end_at == expected_end
