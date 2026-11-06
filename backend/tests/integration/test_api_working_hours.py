from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.models import ChairModel, PatientModel, ServiceModel
from app.domain.model import Chair, Patient, Service
from app.repositories.catalog import ChairRepository, ServiceRepository
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import (
    LOGIN,
    OTHER_PROFESSIONAL_ID,
    PASSWORD,
    PROFESSIONAL_ID,
    insert_professional,
)

pytestmark = pytest.mark.integration

UNKNOWN_PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000999")
PATIENT_ID = UUID("00000000-0000-0000-0000-0000000000c1")
CHAIR_ID = UUID("00000000-0000-0000-0000-0000000000b1")
SERVICE_ID = UUID("00000000-0000-0000-0000-0000000000d1")


def get_future_monday() -> datetime:
    """Calcula el primer lunes que esté al menos 7 días después de hoy (D13)."""
    now = datetime.now(timezone.utc)
    base = now + timedelta(days=7)
    days_ahead = (0 - base.weekday()) % 7
    monday = base + timedelta(days=days_ahead)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


@pytest.fixture(autouse=True)
def clean_working_hours_table(test_engine: Engine, auth_app: object) -> Iterator[None]:
    with Session(test_engine) as session:
        if session.get(PatientModel, PATIENT_ID) is None:
            PatientRepository(session).create(Patient(PATIENT_ID, "Ana Pérez", "30111222", None, None))
        if session.get(ChairModel, CHAIR_ID) is None:
            ChairRepository(session).create(Chair(CHAIR_ID, "Sillón 1", True))
        if session.get(ServiceModel, SERVICE_ID) is None:
            ServiceRepository(session).create(Service(SERVICE_ID, "Consulta", 30, True))
        session.commit()
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM appointment"))
        conn.execute(text("DELETE FROM block"))
        conn.execute(text("DELETE FROM working_hours"))
        conn.execute(
            text(
                "INSERT INTO working_hours (id, professional_id, weekday, start_minute, end_minute) "
                "VALUES (:id, :prof, 1, 540, 780)"
            ),
            {"id": uuid4(), "prof": PROFESSIONAL_ID},
        )
    try:
        yield
    finally:
        with test_engine.begin() as conn:
            conn.execute(text("DELETE FROM appointment"))
            conn.execute(text("DELETE FROM block"))
            conn.execute(text("DELETE FROM working_hours"))


def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def test_reception_gets_working_hours_returns_200(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    res = auth_client.get(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == [{"weekday": 1, "start": "09:00", "end": "13:00"}]


def test_odontologist_gets_own_working_hours_returns_200(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "odontologo")
    res = auth_client.get(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert res.status_code == 200


def test_odontologist_gets_other_professional_working_hours_returns_403(
    auth_client: TestClient,
) -> None:
    headers = token_for(auth_client, "odontologo")
    res = auth_client.get(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json() == {
        "violations": [
            {
                "code": "FORBIDDEN_OPERATION",
                "message": "No tiene permiso para leer horarios.",
            }
        ]
    }


def test_get_working_hours_without_token_returns_401(auth_client: TestClient) -> None:
    res = auth_client.get(f"/api/professionals/{PROFESSIONAL_ID}/working-hours")
    assert res.status_code == 401


def test_get_working_hours_unknown_professional_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.get(
        f"/api/professionals/{UNKNOWN_PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json() == {
        "code": "NOT_FOUND",
        "message": "Profesional no encontrado.",
    }


def test_admin_replaces_working_hours_returns_200(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 2, "start": "08:00", "end": "12:00"}]
    res = auth_client.put(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["workingHours"] == payload

    # Consulta posterior devuelve ese único tramo
    get_res = auth_client.get(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json() == payload


def test_odontologist_replaces_own_working_hours_returns_200(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "odontologo")
    payload = [{"weekday": 1, "start": "09:00", "end": "13:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200


def test_odontologist_replaces_other_professional_working_hours_returns_403(
    auth_client: TestClient,
) -> None:
    headers = token_for(auth_client, "odontologo")
    payload = [{"weekday": 1, "start": "09:00", "end": "13:00"}]
    res = auth_client.put(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403


def test_reception_replaces_working_hours_returns_403(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    payload = [{"weekday": 1, "start": "09:00", "end": "13:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json() == {
        "violations": [
            {
                "code": "FORBIDDEN_OPERATION",
                "message": "No tiene permiso para actualizar horarios.",
            }
        ]
    }


def test_replace_working_hours_with_empty_list_returns_empty(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=[],
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["workingHours"] == []


def test_replace_working_hours_overlapping_returns_422(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    payload = [
        {"weekday": 2, "start": "09:00", "end": "13:00"},
        {"weekday": 2, "start": "12:00", "end": "16:00"},
    ]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["violations"][0]["code"] == "OVERLAPPING_WORKING_HOURS"

    # Conserva su tramo del lunes
    get_res = auth_client.get(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        headers=headers,
    )
    assert get_res.json() == [{"weekday": 1, "start": "09:00", "end": "13:00"}]


def test_replace_working_hours_start_after_end_returns_422(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "13:00", "end": "09:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["violations"][0]["code"] == "INVALID_WORKING_HOURS"


def test_replace_working_hours_malformed_time_returns_400(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "25:00", "end": "26:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 400


def test_replace_working_hours_end_at_24_accepted_returns_200(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 5, "start": "20:00", "end": "24:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["workingHours"] == payload


def test_replace_working_hours_unknown_professional_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.put(
        f"/api/professionals/{UNKNOWN_PROFESSIONAL_ID}/working-hours",
        json=[],
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json() == {
        "code": "NOT_FOUND",
        "message": "Profesional no encontrado.",
    }


def test_replace_working_hours_inactive_professional_accepted(
    auth_client: TestClient, test_engine: Engine
) -> None:
    with test_engine.begin() as conn:
        conn.execute(
            text("UPDATE professional SET active = false WHERE id = :id"),
            {"id": PROFESSIONAL_ID},
        )
    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "09:00", "end": "13:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200


def test_replace_working_hours_reports_outside_appointment_without_cancelling(
    auth_client: TestClient, test_engine: Engine
) -> None:
    monday = get_future_monday()
    # 10:00 a 10:30 local = 13:00 a 13:30 UTC
    start_utc = monday.replace(hour=13, minute=0)
    end_utc = monday.replace(hour=13, minute=30)
    apt_id = uuid4()

    with test_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO appointment (id, patient_id, professional_id, chair_id, service_id, "
                "start_at, end_at, status, created_at, updated_at) "
                "VALUES (:id, :pat, :prof, :chair, :svc, :start, :end, 'reservado', :now, :now)"
            ),
            {
                "id": apt_id,
                "pat": PATIENT_ID,
                "prof": PROFESSIONAL_ID,
                "chair": CHAIR_ID,
                "svc": SERVICE_ID,
                "start": start_utc,
                "end": end_utc,
                "now": datetime.now(timezone.utc),
            },
        )

    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "15:00", "end": "19:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    outside = res.json()["appointmentsOutsideHours"]
    assert len(outside) == 1
    assert outside[0]["id"] == str(apt_id)
    assert outside[0]["patientName"] == "Ana Pérez"
    assert outside[0]["status"] == "reservado"

    with test_engine.begin() as conn:
        status_in_db = conn.execute(
            text("SELECT status FROM appointment WHERE id = :id"),
            {"id": apt_id},
        ).scalar_one()
        assert status_in_db == "reservado"


def test_replace_working_hours_does_not_report_appointment_inside_new_hours(
    auth_client: TestClient, test_engine: Engine
) -> None:
    monday = get_future_monday()
    start_utc = monday.replace(hour=13, minute=0)
    end_utc = monday.replace(hour=13, minute=30)
    apt_id = uuid4()

    with test_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO appointment (id, patient_id, professional_id, chair_id, service_id, "
                "start_at, end_at, status, created_at, updated_at) "
                "VALUES (:id, :pat, :prof, :chair, :svc, :start, :end, 'reservado', :now, :now)"
            ),
            {
                "id": apt_id,
                "pat": PATIENT_ID,
                "prof": PROFESSIONAL_ID,
                "chair": CHAIR_ID,
                "svc": SERVICE_ID,
                "start": start_utc,
                "end": end_utc,
                "now": datetime.now(timezone.utc),
            },
        )

    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "09:00", "end": "12:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["appointmentsOutsideHours"] == []


def test_replace_working_hours_does_not_report_cancelled_appointment(
    auth_client: TestClient, test_engine: Engine
) -> None:
    monday = get_future_monday()
    start_utc = monday.replace(hour=13, minute=0)
    end_utc = monday.replace(hour=13, minute=30)
    apt_id = uuid4()

    with test_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO appointment (id, patient_id, professional_id, chair_id, service_id, "
                "start_at, end_at, status, created_at, updated_at) "
                "VALUES (:id, :pat, :prof, :chair, :svc, :start, :end, 'cancelado', :now, :now)"
            ),
            {
                "id": apt_id,
                "pat": PATIENT_ID,
                "prof": PROFESSIONAL_ID,
                "chair": CHAIR_ID,
                "svc": SERVICE_ID,
                "start": start_utc,
                "end": end_utc,
                "now": datetime.now(timezone.utc),
            },
        )

    headers = token_for(auth_client, "administrador")
    payload = [{"weekday": 1, "start": "15:00", "end": "19:00"}]
    res = auth_client.put(
        f"/api/professionals/{PROFESSIONAL_ID}/working-hours",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["appointmentsOutsideHours"] == []
