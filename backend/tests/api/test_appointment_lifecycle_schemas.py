from datetime import datetime, timezone
from uuid import UUID
from pydantic import ValidationError
import pytest

from app.api.schemas import (
    HistoryEntryResponse,
    RescheduleDetailResponse,
    RescheduleInput,
    StatusChangeInput,
)


def test_status_change_input_valid_statuses() -> None:
    for status in ("confirmado", "atendido", "ausente"):
        model = StatusChangeInput.model_validate({"toStatus": status})
        assert model.to_status == status


def test_status_change_input_cancelado_rejected() -> None:
    with pytest.raises(ValidationError):
        StatusChangeInput.model_validate({"toStatus": "cancelado"})


def test_status_change_input_reservado_rejected() -> None:
    with pytest.raises(ValidationError):
        StatusChangeInput.model_validate({"toStatus": "reservado"})



def test_status_change_input_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        StatusChangeInput.model_validate({"toStatus": "confirmado", "note": "una nota"})


def test_reschedule_input_start_at_with_tz_accepted() -> None:
    data = {
        "startAt": "2026-11-16T11:00:00-03:00",
        "professionalId": "00000000-0000-0000-0000-000000000002",
        "chairId": "00000000-0000-0000-0000-0000000000b2",
        "durationMin": 60,
    }
    model = RescheduleInput.model_validate(data)
    assert model.start_at.tzinfo is not None
    assert model.professional_id == UUID("00000000-0000-0000-0000-000000000002")
    assert model.chair_id == UUID("00000000-0000-0000-0000-0000000000b2")
    assert model.duration_min == 60


def test_reschedule_input_minimal_accepted() -> None:
    model = RescheduleInput.model_validate({"startAt": "2026-11-16T11:00:00-03:00"})
    assert model.start_at.tzinfo is not None
    assert model.professional_id is None
    assert model.chair_id is None
    assert model.duration_min is None


def test_reschedule_input_start_at_without_tz_rejected() -> None:
    with pytest.raises(ValidationError):
        RescheduleInput.model_validate({"startAt": "2026-11-16T11:00:00"})


def test_reschedule_input_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        RescheduleInput.model_validate({
            "startAt": "2026-11-16T11:00:00-03:00",
            "status": "cancelado",
        })


def test_history_entry_initial_entry_serializes_from_and_reschedule_as_null() -> None:
    entry = HistoryEntryResponse(
        from_status=None,
        to_status="reservado",
        changed_by=UUID("00000000-0000-0000-0000-0000000000e2"),
        changed_by_name="Recepción Demo",
        changed_at="2026-11-16T10:00:00Z",
        reschedule=None,
    )
    dumped = entry.model_dump(by_alias=True)
    assert "from" in dumped
    assert dumped["from"] is None
    assert dumped["to"] == "reservado"
    assert dumped["changedBy"] == UUID("00000000-0000-0000-0000-0000000000e2")
    assert dumped["changedByName"] == "Recepción Demo"
    assert dumped["changedAt"] == "2026-11-16T10:00:00Z"
    assert "reschedule" in dumped
    assert dumped["reschedule"] is None


def test_history_entry_reschedule_detail_flat_eight_fields() -> None:
    reschedule_detail = RescheduleDetailResponse(
        previous_start_at="2026-11-16T13:00:00Z",
        previous_end_at="2026-11-16T13:30:00Z",
        new_start_at="2026-11-16T14:00:00Z",
        new_end_at="2026-11-16T14:30:00Z",
        previous_professional_id=UUID("00000000-0000-0000-0000-000000000001"),
        new_professional_id=UUID("00000000-0000-0000-0000-000000000002"),
        previous_chair_id=UUID("00000000-0000-0000-0000-0000000000b1"),
        new_chair_id=UUID("00000000-0000-0000-0000-0000000000b2"),
    )
    entry = HistoryEntryResponse(
        from_status="confirmado",
        to_status="reservado",
        changed_by=UUID("00000000-0000-0000-0000-0000000000e2"),
        changed_by_name="Recepción Demo",
        changed_at="2026-11-16T14:00:00Z",
        reschedule=reschedule_detail,
    )
    dumped = entry.model_dump(by_alias=True)
    assert dumped["from"] == "confirmado"
    assert dumped["to"] == "reservado"
    res = dumped["reschedule"]
    assert isinstance(res, dict)
    assert len(res) == 8
    assert res["previousStartAt"] == "2026-11-16T13:00:00Z"
    assert res["previousEndAt"] == "2026-11-16T13:30:00Z"
    assert res["newStartAt"] == "2026-11-16T14:00:00Z"
    assert res["newEndAt"] == "2026-11-16T14:30:00Z"
    assert res["previousProfessionalId"] == UUID("00000000-0000-0000-0000-000000000001")
    assert res["newProfessionalId"] == UUID("00000000-0000-0000-0000-000000000002")
    assert res["previousChairId"] == UUID("00000000-0000-0000-0000-0000000000b1")
    assert res["newChairId"] == UUID("00000000-0000-0000-0000-0000000000b2")

