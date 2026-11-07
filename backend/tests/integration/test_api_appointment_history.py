from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
)
from app.demo_data import CHAIRS, PATIENTS, PROFESSIONALS, SERVICES, USERS
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import (
    ADMIN_ID,
    LOGIN,
    PASSWORD,
    PROFESSIONAL_ID,
    RECEPTION_ID,
    create_auth_users,
)
from tests.integration.conftest import clean_database_tables

pytestmark = pytest.mark.integration

P1_ID = PROFESSIONALS[0].id
P2_ID = PROFESSIONALS[1].id
CHAIR_1_ID = CHAIRS[0].id
CHAIR_2_ID = CHAIRS[1].id
SERVICE_CONTROL_ID = SERVICES[3].id
PATIENT_1_ID = PATIENTS[0].id
PATIENT_2_ID = PATIENTS[1].id

TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")


def get_future_monday() -> datetime:
    now = datetime.now(timezone.utc)
    base = now + timedelta(days=7)
    days_ahead = (0 - base.weekday()) % 7
    monday = base + timedelta(days=days_ahead)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


@pytest.fixture(autouse=True)
def setup_tables(test_engine: Engine, auth_app: object) -> Iterator[None]:
    clean_database_tables(test_engine)
    create_auth_users(test_engine)

    with Session(test_engine) as session:
        prof_repo = ProfessionalRepository(session)
        for p in PROFESSIONALS:
            if prof_repo.get_by_id(p.id) is None:
                prof_repo.create(p)

        chair_repo = ChairRepository(session)
        for c in CHAIRS:
            if chair_repo.get_by_id(c.id) is None:
                chair_repo.create(c)

        serv_repo = ServiceRepository(session)
        for s in SERVICES:
            if serv_repo.get_by_id(s.id) is None:
                serv_repo.create(s)

        pat_repo = PatientRepository(session)
        for pat in PATIENTS:
            if pat_repo.get_by_id(pat.id) is None:
                pat_repo.create(pat)

        session.commit()

    with test_engine.begin() as conn:
        for u in USERS:
            conn.execute(
                text("UPDATE app_user SET display_name = :name WHERE id = :id"),
                {"id": u.id, "name": u.display_name},
            )
        conn.execute(
            text(
                "INSERT INTO working_hours (id, professional_id, weekday, start_minute, end_minute) "
                "VALUES (:id1, :p1, 1, 540, 780), (:id2, :p2, 1, 540, 780)"
            ),
            {"id1": uuid4(), "p1": P1_ID, "id2": uuid4(), "p2": P2_ID},
        )


    try:
        yield
    finally:
        clean_database_tables(test_engine)


def create_future_appointment(
    client: TestClient,
    headers: dict[str, str],
    monday: datetime,
    start_hour: int = 10,
    prof_id: UUID = P1_ID,
    chair_id: UUID = CHAIR_1_ID,
    pat_id: UUID = PATIENT_1_ID,
    serv_id: UUID = SERVICE_CONTROL_ID,
) -> UUID:
    start_dt = datetime(monday.year, monday.month, monday.day, start_hour, 0, tzinfo=TZ_BA)
    res = client.post(
        "/api/appointments",
        headers=headers,
        json={
            "patientId": str(pat_id),
            "professionalId": str(prof_id),
            "chairId": str(chair_id),
            "serviceId": str(serv_id),
            "startAt": start_dt.isoformat(),
        },
    )
    assert res.status_code == 201, res.text
    return UUID(res.json()["id"])


def test_history_ascending_with_creation_and_changed_by_name(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, reception_headers, monday, start_hour=10)

    # Confirmar el turno con recepción
    conf_res = auth_client.post(
        f"/api/appointments/{app_id}/status",
        headers=reception_headers,
        json={"toStatus": "confirmado"},
    )
    assert conf_res.status_code == 200

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=reception_headers)
    assert res.status_code == 200, res.text
    entries = res.json()
    assert len(entries) == 2

    first = entries[0]
    assert first["from"] is None
    assert first["to"] == "reservado"
    assert first["changedBy"] == str(RECEPTION_ID)
    assert first["changedByName"] == "Recepción Demo"
    assert first["reschedule"] is None

    second = entries[1]
    assert second["from"] == "reservado"
    assert second["to"] == "confirmado"
    assert second["changedBy"] == str(RECEPTION_ID)
    assert second["changedByName"] == "Recepción Demo"
    assert second["reschedule"] is None
    assert second["changedAt"] >= first["changedAt"]


def test_history_reschedule_entry_has_to_reservado_and_flat_detail(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    admin_headers = token_for(auth_client, "administrador")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, reception_headers, monday, start_hour=10)

    # Confirmar
    auth_client.post(
        f"/api/appointments/{app_id}/status",
        headers=reception_headers,
        json={"toStatus": "confirmado"},
    )

    # Reprogramar a las 11:00
    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res_sched = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=reception_headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res_sched.status_code == 200

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=admin_headers)
    assert res.status_code == 200, res.text
    entries = res.json()
    assert len(entries) == 3

    last = entries[-1]
    assert last["from"] == "confirmado"
    assert last["to"] == "reservado"
    assert last["changedBy"] == str(RECEPTION_ID)
    assert last["changedByName"] == "Recepción Demo"
    assert last["changedAt"] >= entries[1]["changedAt"]

    detail = last["reschedule"]
    assert detail is not None
    assert isinstance(detail, dict)
    assert len(detail) == 8
    assert "previousStartAt" in detail
    assert "previousEndAt" in detail
    assert "newStartAt" in detail
    assert "newEndAt" in detail
    assert detail["previousProfessionalId"] == str(P1_ID)
    assert detail["newProfessionalId"] == str(P1_ID)
    assert detail["previousChairId"] == str(CHAIR_1_ID)
    assert detail["newChairId"] == str(CHAIR_1_ID)


def test_history_nonexistent_appointment_returns_404(auth_client: TestClient) -> None:
    admin_headers = token_for(auth_client, "administrador")
    res = auth_client.get(
        "/api/appointments/00000000-0000-0000-0000-000000000999/history",
        headers=admin_headers,
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Turno no encontrado."}


def test_dentist_reads_own_appointment_history_returns_200(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    dentist_headers = token_for(auth_client, "odontologo")
    monday = get_future_monday()
    app_id = create_future_appointment(
        auth_client, reception_headers, monday, start_hour=10, prof_id=PROFESSIONAL_ID
    )

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=dentist_headers)
    assert res.status_code == 200, res.text
    entries = res.json()
    assert isinstance(entries, list)
    assert len(entries) >= 1
    assert entries[0]["from"] is None
    assert entries[0]["to"] == "reservado"


def test_dentist_reads_other_professional_history_returns_403(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    dentist_headers = token_for(auth_client, "odontologo")
    monday = get_future_monday()
    # Turno con P2 (no es la Dra. Laura Quiroga)
    app_id = create_future_appointment(
        auth_client,
        reception_headers,
        monday,
        start_hour=10,
        prof_id=P2_ID,
        chair_id=CHAIR_2_ID,
        pat_id=PATIENT_2_ID,
    )

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=dentist_headers)
    assert res.status_code == 403, res.text
    data = res.json()
    violations = data["violations"]
    assert any(
        v["code"] == "FORBIDDEN_OPERATION" and "No tiene permiso para leer el historial de turnos." in v["message"]
        for v in violations
    )
    # Does not expose appointment details in body
    assert "startAt" not in data
    assert "professionalId" not in data


def test_reception_reads_other_professional_history_returns_200(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(
        auth_client,
        reception_headers,
        monday,
        start_hour=10,
        prof_id=P2_ID,
        chair_id=CHAIR_2_ID,
        pat_id=PATIENT_2_ID,
    )

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=reception_headers)
    assert res.status_code == 200, res.text
    entries = res.json()
    assert len(entries) >= 1


def test_admin_reads_other_professional_history_returns_200(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    admin_headers = token_for(auth_client, "administrador")
    monday = get_future_monday()
    app_id = create_future_appointment(
        auth_client,
        reception_headers,
        monday,
        start_hour=10,
        prof_id=P1_ID,
        chair_id=CHAIR_1_ID,
        pat_id=PATIENT_1_ID,
    )

    res = auth_client.get(f"/api/appointments/{app_id}/history", headers=admin_headers)
    assert res.status_code == 200, res.text
    entries = res.json()
    assert len(entries) >= 1
