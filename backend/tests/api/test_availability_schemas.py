from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo
from pydantic import ValidationError
import pytest

from app.api.schemas import (
    AffectedAppointmentResponse,
    BlockCreateResponse,
    BlockInput,
    BlockResponse,
    BlocksQuery,
    WorkingHoursResponse,
    WorkingHoursSlotInput,
    format_utc_iso,
)


def test_working_hours_slot_valid_and_24_end() -> None:
    slot = WorkingHoursSlotInput.model_validate({"weekday": 1, "start": "09:00", "end": "13:00"})
    assert slot.weekday == 1
    assert slot.start == "09:00"
    assert slot.end == "13:00"

    slot_24 = WorkingHoursSlotInput.model_validate({"weekday": 5, "start": "20:00", "end": "24:00"})
    assert slot_24.end == "24:00"


def test_working_hours_slot_rejects_25_and_24_start() -> None:
    with pytest.raises(ValidationError):
        WorkingHoursSlotInput.model_validate({"weekday": 1, "start": "25:00", "end": "26:00"})

    with pytest.raises(ValidationError):
        WorkingHoursSlotInput.model_validate({"weekday": 1, "start": "24:00", "end": "24:00"})

    with pytest.raises(ValidationError):
        WorkingHoursSlotInput.model_validate({"weekday": 1, "start": "09:00", "end": "25:00"})


def test_working_hours_slot_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        WorkingHoursSlotInput.model_validate({
            "weekday": 1,
            "start": "09:00",
            "end": "13:00",
            "extra": "forbidden",
        })


def test_block_input_timezone_mandatory() -> None:
    valid = BlockInput.model_validate({
        "startAt": "2026-12-07T09:00:00-03:00",
        "endAt": "2026-12-07T13:00:00-03:00",
        "reason": "Congreso",
    })
    assert valid.start_at.tzinfo is not None
    assert valid.end_at.tzinfo is not None
    assert valid.reason == "Congreso"

    with pytest.raises(ValidationError):
        BlockInput.model_validate({
            "startAt": "2026-12-07T09:00:00",
            "endAt": "2026-12-07T13:00:00",
        })

    with pytest.raises(ValidationError):
        BlockInput.model_validate({
            "startAt": "2026-12-07T09:00:00-03:00",
            "endAt": "2026-12-07T13:00:00-03:00",
            "extra": "forbidden",
        })


def test_blocks_query_filter_timezone_mandatory() -> None:
    q = BlocksQuery.model_validate({
        "from": "2026-12-07T00:00:00-03:00",
        "to": "2026-12-14T00:00:00-03:00",
    })
    assert q.from_time is not None and q.from_time.tzinfo is not None
    assert q.to_time is not None and q.to_time.tzinfo is not None

    q_empty = BlocksQuery.model_validate({})
    assert q_empty.from_time is None
    assert q_empty.to_time is None

    with pytest.raises(ValidationError):
        BlocksQuery.model_validate({"from": "2026-12-07T00:00:00"})

    with pytest.raises(ValidationError):
        BlocksQuery.model_validate({"to": "2026-12-14T00:00:00"})


def test_affected_appointment_response_camelcase() -> None:
    uid = UUID("00000000-0000-0000-0000-000000000071")
    pat_id = UUID("00000000-0000-0000-0000-0000000000c1")
    chair_id = UUID("00000000-0000-0000-0000-0000000000b1")
    dt_start = datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc)
    dt_end = datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc)

    resp = AffectedAppointmentResponse(
        id=uid,
        patient_id=pat_id,
        patient_name="Ana Pérez",
        chair_id=chair_id,
        start_at=format_utc_iso(dt_start),
        end_at=format_utc_iso(dt_end),
        status="reservado",
    )
    dumped = resp.model_dump(by_alias=True, mode="json")
    assert dumped == {
        "id": str(uid),
        "patientId": str(pat_id),
        "patientName": "Ana Pérez",
        "chairId": str(chair_id),
        "startAt": "2026-12-07T13:00:00Z",
        "endAt": "2026-12-07T13:30:00Z",
        "status": "reservado",
    }
