from datetime import datetime, timezone
from uuid import UUID
from pydantic import ValidationError
import pytest

from app.api.schemas import (
    AppointmentInput,
    AppointmentResponse,
    format_utc_iso,
)


def test_appointment_input_start_at_with_tz_accepted() -> None:
    data = {
        "patientId": "00000000-0000-0000-0000-0000000000c1",
        "professionalId": "00000000-0000-0000-0000-000000000001",
        "chairId": "00000000-0000-0000-0000-0000000000b1",
        "serviceId": "00000000-0000-0000-0000-0000000000d4",
        "startAt": "2026-11-16T10:00:00-03:00",
    }
    model = AppointmentInput.model_validate(data)
    assert model.start_at.tzinfo is not None
    assert model.patient_id == UUID("00000000-0000-0000-0000-0000000000c1")


def test_appointment_input_start_at_without_tz_rejected() -> None:
    data = {
        "patientId": "00000000-0000-0000-0000-0000000000c1",
        "professionalId": "00000000-0000-0000-0000-000000000001",
        "chairId": "00000000-0000-0000-0000-0000000000b1",
        "serviceId": "00000000-0000-0000-0000-0000000000d4",
        "startAt": "2026-11-16T10:00:00",
    }
    with pytest.raises(ValidationError):
        AppointmentInput.model_validate(data)


def test_appointment_input_extra_field_forbidden() -> None:
    data = {
        "patientId": "00000000-0000-0000-0000-0000000000c1",
        "professionalId": "00000000-0000-0000-0000-000000000001",
        "chairId": "00000000-0000-0000-0000-0000000000b1",
        "serviceId": "00000000-0000-0000-0000-0000000000d4",
        "startAt": "2026-11-16T10:00:00-03:00",
        "status": "reservado",
    }
    with pytest.raises(ValidationError):
        AppointmentInput.model_validate(data)


def test_appointment_input_optional_duration_min() -> None:
    data_with_duration = {
        "patientId": "00000000-0000-0000-0000-0000000000c1",
        "professionalId": "00000000-0000-0000-0000-000000000001",
        "chairId": "00000000-0000-0000-0000-0000000000b1",
        "serviceId": "00000000-0000-0000-0000-0000000000d4",
        "startAt": "2026-11-16T10:00:00-03:00",
        "durationMin": 45,
    }
    model = AppointmentInput.model_validate(data_with_duration)
    assert model.duration_min == 45

    data_without_duration = {
        "patientId": "00000000-0000-0000-0000-0000000000c1",
        "professionalId": "00000000-0000-0000-0000-000000000001",
        "chairId": "00000000-0000-0000-0000-0000000000b1",
        "serviceId": "00000000-0000-0000-0000-0000000000d4",
        "startAt": "2026-11-16T10:00:00-03:00",
    }
    model_none = AppointmentInput.model_validate(data_without_duration)
    assert model_none.duration_min is None


def test_appointment_response_camelcase_and_utc() -> None:
    uid = UUID("00000000-0000-0000-0000-000000000071")
    pat_id = UUID("00000000-0000-0000-0000-0000000000c1")
    prof_id = UUID("00000000-0000-0000-0000-000000000001")
    chair_id = UUID("00000000-0000-0000-0000-0000000000b1")
    serv_id = UUID("00000000-0000-0000-0000-0000000000d4")
    dt_start = datetime(2026, 11, 16, 13, 0, tzinfo=timezone.utc)
    dt_end = datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc)

    resp = AppointmentResponse(
        id=uid,
        patient_id=pat_id,
        professional_id=prof_id,
        chair_id=chair_id,
        service_id=serv_id,
        start_at=format_utc_iso(dt_start),
        end_at=format_utc_iso(dt_end),
        status="reservado",
    )
    dumped = resp.model_dump(by_alias=True, mode="json")
    assert dumped == {
        "id": str(uid),
        "patientId": str(pat_id),
        "professionalId": str(prof_id),
        "chairId": str(chair_id),
        "serviceId": str(serv_id),
        "startAt": "2026-11-16T13:00:00Z",
        "endAt": "2026-11-16T13:30:00Z",
        "status": "reservado",
    }
