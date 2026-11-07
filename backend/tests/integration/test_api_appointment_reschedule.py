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
    BlockModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
)
from app.demo_data import CHAIRS, PATIENTS, PROFESSIONALS, SERVICES
from app.repositories.appointment import AppointmentStatusChangeRepository
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
SERVICE_CLEANING_ID = SERVICES[0].id  # 45 min
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
    duration_min: int | None = None,
    prof_id: UUID = P1_ID,
    chair_id: UUID = CHAIR_1_ID,
    pat_id: UUID = PATIENT_1_ID,
    serv_id: UUID = SERVICE_CONTROL_ID,
) -> UUID:
    start_dt = datetime(monday.year, monday.month, monday.day, start_hour, 0, tzinfo=TZ_BA)
    payload: dict[str, object] = {
        "patientId": str(pat_id),
        "professionalId": str(prof_id),
        "chairId": str(chair_id),
        "serviceId": str(serv_id),
        "startAt": start_dt.isoformat(),
    }
    if duration_min is not None:
        payload["durationMin"] = duration_min
    res = client.post("/api/appointments", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return UUID(res.json()["id"])


def test_reschedule_start_only_preserves_real_duration_and_returns_to_reservado(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10, duration_min=45)

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "reservado"
    assert data["professionalId"] == str(P1_ID)
    assert data["chairId"] == str(CHAIR_1_ID)

    expected_start_utc = new_start_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    expected_end_utc = (new_start_dt + timedelta(minutes=45)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert data["startAt"] == expected_start_utc
    assert data["endAt"] == expected_end_utc


def test_reschedule_with_explicit_professional_chair_and_duration(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "administrador")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10, duration_min=30)

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={
            "startAt": new_start_dt.isoformat(),
            "professionalId": str(P2_ID),
            "chairId": str(CHAIR_2_ID),
            "durationMin": 60,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "reservado"
    assert data["professionalId"] == str(P2_ID)
    assert data["chairId"] == str(CHAIR_2_ID)
    expected_end_utc = (new_start_dt + timedelta(minutes=60)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert data["endAt"] == expected_end_utc


def test_reschedule_professional_overlap_returns_409(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    # Turno 1 con P1 de 10:00 a 10:30
    _app1 = create_future_appointment(auth_client, headers, monday, start_hour=10, prof_id=P1_ID, chair_id=CHAIR_1_ID)
    # Turno 2 con P2 de 10:00 a 10:30
    app2 = create_future_appointment(
        auth_client, headers, monday, start_hour=10, prof_id=P2_ID, chair_id=CHAIR_2_ID, pat_id=PATIENT_2_ID
    )

    # Intento de reprogramar Turno 2 a las 10:00 con P1
    new_start_dt = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app2}/reschedule",
        headers=headers,
        json={
            "startAt": new_start_dt.isoformat(),
            "professionalId": str(P1_ID),
        },
    )
    assert res.status_code == 409, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "PROFESSIONAL_OVERLAP" for v in violations)


def test_reschedule_chair_overlap_returns_409(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    # Turno 1 en CHAIR 1 de 10:00 a 10:30
    _app1 = create_future_appointment(auth_client, headers, monday, start_hour=10, prof_id=P1_ID, chair_id=CHAIR_1_ID)
    # Turno 2 en CHAIR 2 de 10:00 a 10:30
    app2 = create_future_appointment(
        auth_client, headers, monday, start_hour=10, prof_id=P2_ID, chair_id=CHAIR_2_ID, pat_id=PATIENT_2_ID
    )

    # Intento de reprogramar Turno 2 a las 10:00 en CHAIR 1
    new_start_dt = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app2}/reschedule",
        headers=headers,
        json={
            "startAt": new_start_dt.isoformat(),
            "chairId": str(CHAIR_1_ID),
        },
    )
    assert res.status_code == 409, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "CHAIR_OVERLAP" for v in violations)


def test_reschedule_inside_block_returns_409(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    # Bloqueo para P1 de 09:00 a 13:00
    block_start = datetime(monday.year, monday.month, monday.day, 9, 0, tzinfo=TZ_BA)
    block_end = datetime(monday.year, monday.month, monday.day, 13, 0, tzinfo=TZ_BA)
    with test_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO block (id, professional_id, start_at, end_at, reason) "
                "VALUES (:id, :p, :start, :end, 'Capacitación')"
            ),
            {"id": uuid4(), "p": P1_ID, "start": block_start, "end": block_end},
        )

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res.status_code == 409, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "BLOCKED_TIME" for v in violations)


def test_reschedule_outside_working_hours_returns_409(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    outside_dt = datetime(monday.year, monday.month, monday.day, 18, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={"startAt": outside_dt.isoformat()},
    )
    assert res.status_code == 409, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "OUTSIDE_WORKING_HOURS" for v in violations)


def test_reschedule_in_the_past_returns_422(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    yesterday_min = (yesterday.minute // 5) * 5
    past_dt = yesterday.replace(minute=yesterday_min, second=0, microsecond=0)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={"startAt": past_dt.isoformat()},
    )
    assert res.status_code == 422, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "IN_THE_PAST" for v in violations)


def test_reschedule_start_at_without_timezone_returns_400(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={"startAt": f"{monday.year:04d}-{monday.month:02d}-{monday.day:02d}T11:00:00"},
    )
    assert res.status_code == 400


def test_reschedule_extra_field_returns_400(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=headers,
        json={
            "startAt": new_start_dt.isoformat(),
            "status": "cancelado",
        },
    )
    assert res.status_code == 400


def test_reschedule_nonexistent_appointment_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        "/api/appointments/00000000-0000-0000-0000-000000000999/reschedule",
        headers=headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Turno no encontrado."}


def test_dentist_cannot_reschedule_returns_403(
    auth_client: TestClient, test_engine: Engine
) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    dentist_headers = token_for(auth_client, "odontologo")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, reception_headers, monday, prof_id=PROFESSIONAL_ID)

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=dentist_headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res.status_code == 403, res.text
    violations = res.json()["violations"]
    assert any(
        v["code"] == "FORBIDDEN_OPERATION" and "No tiene permiso para reprogramar turnos." in v["message"]
        for v in violations
    )


def test_reschedule_terminal_state_appointment_returns_422(
    auth_client: TestClient, test_engine: Engine
) -> None:
    admin_headers = token_for(auth_client, "administrador")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, admin_headers, monday, start_hour=10)

    # Cancelar el turno
    cancel_res = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=admin_headers)
    assert cancel_res.status_code == 200

    new_start_dt = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=TZ_BA)
    res = auth_client.post(
        f"/api/appointments/{app_id}/reschedule",
        headers=admin_headers,
        json={"startAt": new_start_dt.isoformat()},
    )
    assert res.status_code == 422, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "INVALID_TRANSITION" for v in violations)
