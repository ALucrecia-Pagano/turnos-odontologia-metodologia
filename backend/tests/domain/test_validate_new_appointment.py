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
    Chair,
    NewAppointmentRequest,
    Patient,
    Professional,
    ScheduleContext,
    Service,
)
from app.domain.violations import Ok, ReferenceKind, Rejected, ViolationCode

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

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")
CTX = ScheduleContext(tz=BUENOS_AIRES)


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
