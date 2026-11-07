from datetime import date, timedelta
from uuid import UUID

from app.api.schemas import (
    AgendaAppointmentResponse,
    AgendaResponse,
    AgendaWorkingHoursResponse,
    BlockResponse,
)

DAY = date.today() + timedelta(days=30)
DAY_ISO = DAY.isoformat()
LAST_DAY = DAY + timedelta(days=6)

APPOINTMENT_ID = UUID("00000000-0000-0000-0000-0000000000a1")
PATIENT_ID = UUID("00000000-0000-0000-0000-0000000000c1")
PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000001")
CHAIR_ID = UUID("00000000-0000-0000-0000-0000000000b1")
SERVICE_ID = UUID("00000000-0000-0000-0000-0000000000d4")
BLOCK_ID = UUID("00000000-0000-0000-0000-0000000000f1")


def build_appointment(status: str = "reservado") -> AgendaAppointmentResponse:
    return AgendaAppointmentResponse(
        id=APPOINTMENT_ID,
        patient_id=PATIENT_ID,
        patient_name="Ana Pérez",
        professional_id=PROFESSIONAL_ID,
        professional_name="Dra. Laura Quiroga",
        chair_id=CHAIR_ID,
        chair_name="Sillón 1",
        service_id=SERVICE_ID,
        service_name="Control",
        start_at=f"{DAY_ISO}T13:00:00Z",
        end_at=f"{DAY_ISO}T13:30:00Z",
        status=status,
    )


def test_agenda_appointment_response_serializes_names_in_camel_case() -> None:
    data = build_appointment("cancelado").model_dump(by_alias=True, mode="json")
    assert data == {
        "id": str(APPOINTMENT_ID),
        "patientId": str(PATIENT_ID),
        "patientName": "Ana Pérez",
        "professionalId": str(PROFESSIONAL_ID),
        "professionalName": "Dra. Laura Quiroga",
        "chairId": str(CHAIR_ID),
        "chairName": "Sillón 1",
        "serviceId": str(SERVICE_ID),
        "serviceName": "Control",
        "startAt": f"{DAY_ISO}T13:00:00Z",
        "endAt": f"{DAY_ISO}T13:30:00Z",
        "status": "cancelado",
    }


def test_agenda_working_hours_response_keeps_hh_mm_including_24_00() -> None:
    slot = AgendaWorkingHoursResponse(
        professional_id=PROFESSIONAL_ID, weekday=1, start="23:00", end="24:00"
    )
    assert slot.model_dump(by_alias=True, mode="json") == {
        "professionalId": str(PROFESSIONAL_ID),
        "weekday": 1,
        "start": "23:00",
        "end": "24:00",
    }


def test_agenda_response_envelope_uses_from_to_and_timezone() -> None:
    block = BlockResponse(
        id=BLOCK_ID,
        professional_id=PROFESSIONAL_ID,
        start_at=f"{DAY_ISO}T17:00:00Z",
        end_at=f"{DAY_ISO}T18:00:00Z",
        reason="Congreso",
    )
    envelope = AgendaResponse(
        from_date=DAY,
        to_date=LAST_DAY,
        timezone="America/Argentina/Buenos_Aires",
        appointments=[build_appointment()],
        working_hours=[
            AgendaWorkingHoursResponse(
                professional_id=PROFESSIONAL_ID, weekday=1, start="09:00", end="13:00"
            )
        ],
        blocks=[block],
    )
    data = envelope.model_dump(by_alias=True, mode="json")
    assert list(data) == ["from", "to", "timezone", "appointments", "workingHours", "blocks"]
    assert data["from"] == DAY_ISO
    assert data["to"] == LAST_DAY.isoformat()
    assert data["timezone"] == "America/Argentina/Buenos_Aires"
    assert data["appointments"][0]["status"] == "reservado"
    assert data["workingHours"][0]["start"] == "09:00"
    assert data["blocks"][0] == {
        "id": str(BLOCK_ID),
        "professionalId": str(PROFESSIONAL_ID),
        "startAt": f"{DAY_ISO}T17:00:00Z",
        "endAt": f"{DAY_ISO}T18:00:00Z",
        "reason": "Congreso",
    }
