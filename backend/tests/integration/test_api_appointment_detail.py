from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from tests.integration.agenda_api_support import (
    CHAIR_1_ID,
    CHAIR_2_ID,
    P1_ID,
    P2_ID,
    PATIENT_1_ID,
    PATIENT_2_ID,
    SERVICE_CONTROL_ID,
    UNKNOWN_ID,
    agenda_data,
    book,
    cancel,
    future_monday,
    local_at,
    token_for,
    utc_z,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("agenda_data")]

__all__ = ["agenda_data"]


def test_detail_returns_the_enriched_appointment(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    start = local_at(future_monday(), 10)
    appointment_id = book(auth_client, headers, start)

    res = auth_client.get(f"/api/appointments/{appointment_id}", headers=headers)

    assert res.status_code == 200, res.text
    assert res.json() == {
        "id": appointment_id,
        "patientId": str(PATIENT_1_ID),
        "patientName": "Ana Pérez",
        "professionalId": str(P1_ID),
        "professionalName": "Dra. Laura Quiroga",
        "chairId": str(CHAIR_1_ID),
        "chairName": "Sillón 1",
        "serviceId": str(SERVICE_CONTROL_ID),
        "serviceName": "Control",
        "startAt": utc_z(start),
        "endAt": utc_z(start + timedelta(minutes=30)),
        "status": "reservado",
    }
    assert res.json()["startAt"] == f"{future_monday().isoformat()}T13:00:00Z"


def test_detail_shows_the_current_status_of_a_cancelled_appointment(
    auth_client: TestClient,
) -> None:
    headers = token_for(auth_client, "administrador")
    appointment_id = book(auth_client, headers, local_at(future_monday(), 11))
    cancel(auth_client, headers, appointment_id)

    res = auth_client.get(f"/api/appointments/{appointment_id}", headers=headers)

    assert res.status_code == 200, res.text
    assert res.json()["status"] == "cancelado"


def test_detail_of_unknown_appointment_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")

    res = auth_client.get(f"/api/appointments/{UNKNOWN_ID}", headers=headers)

    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Turno no encontrado."}


def test_detail_with_malformed_uuid_returns_400(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")

    res = auth_client.get("/api/appointments/no-es-un-uuid", headers=headers)

    assert res.status_code == 400
    assert res.json() == {
        "errors": [{"field": "id", "type": "uuid_parsing", "message": "Dato inválido."}]
    }


def test_detail_without_token_returns_401(auth_client: TestClient) -> None:
    res = auth_client.get(f"/api/appointments/{UNKNOWN_ID}")

    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_TOKEN"


def test_dentist_reads_the_detail_of_another_professionals_appointment(
    auth_client: TestClient,
) -> None:
    reception = token_for(auth_client, "recepcion")
    appointment_id = book(
        auth_client,
        reception,
        local_at(future_monday(), 9),
        professional_id=P2_ID,
        chair_id=CHAIR_2_ID,
        patient_id=PATIENT_2_ID,
    )
    dentist = token_for(auth_client, "odontologo")

    res = auth_client.get(f"/api/appointments/{appointment_id}", headers=dentist)

    assert res.status_code == 200, res.text
    assert res.json()["professionalId"] == str(P2_ID)
    assert res.json()["professionalName"] == "Dr. Martín Sosa"
