from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.domain.appointment import validate_new_appointment
from app.domain.model import Appointment, AppointmentStatus, NewAppointmentRequest, Service
from app.domain.violations import Ok, Rejected, ViolationCode

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


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 20, hour, minute, tzinfo=timezone.utc)


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
        start_at=start_at,
        duration_min=duration_min,
    )


def test_validate_new_appointment_free_professional_and_chair_returns_ok_with_reserved_appointment() -> (
    None
):
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(_request(_at(13)), service, [])

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

    result = validate_new_appointment(_request(_at(13), duration_min=20), service, [])

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

    result = validate_new_appointment(_request(_at(13), duration_min=explicit_min), service, [])

    assert _ok_end(result) == expected_end


def test_validate_new_appointment_start_in_buenos_aires_time_returns_utc_appointment() -> None:
    service = Service(id=SVC_30, default_duration_min=30)
    start_local = datetime(2026, 10, 20, 10, 0, tzinfo=timezone(timedelta(hours=-3)))

    result = validate_new_appointment(_request(start_local), service, [])

    assert isinstance(result, Ok)
    assert result.appointment.start_at.isoformat() == "2026-10-20T13:00:00+00:00"
    assert result.appointment.end_at.isoformat() == "2026-10-20T13:30:00+00:00"


def _summary(result: object) -> list[tuple[ViolationCode, UUID | None]]:
    assert isinstance(result, Rejected)
    return [(v.code, v.conflicting_appointment_id) for v in result.violations]


def test_validate_new_appointment_explicit_zero_duration_is_rejected_as_invalid_duration() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(_request(_at(13), duration_min=0), service, [])

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

    result = validate_new_appointment(_request(_at(13), duration_min=explicit_min), service, [])

    assert _summary(result) == [(ViolationCode.INVALID_DURATION, None)]


def test_validate_new_appointment_invalid_duration_message_mentions_received_value() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(_request(_at(13), duration_min=-15), service, [])

    assert isinstance(result, Rejected)
    assert "-15" in result.violations[0].message
    assert result.violations[0].message == (
        "La duración del turno debe ser mayor que cero minutos (se recibió -15)."
    )


def test_validate_new_appointment_same_professional_overlap_is_rejected_with_conflicting_id() -> None:
    service = Service(id=SVC_30, default_duration_min=30)

    result = validate_new_appointment(
        _request(_at(13, 15), chair_id=S2), service, [_appt_a()]
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
        request, Service(id=SVC_30, default_duration_min=default_min), existing
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
