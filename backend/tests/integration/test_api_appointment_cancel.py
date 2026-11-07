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



def create_past_appointment(
    engine: Engine,
    status: str,
    professional_id: UUID = P1_ID,
    patient_id: UUID = PATIENT_1_ID,
    chair_id: UUID = CHAIR_1_ID,
    service_id: UUID = SERVICE_CONTROL_ID,
    hours_ago: int = 2,
) -> UUID:
    now = datetime.now(timezone.utc)
    minute = (now.minute // 5) * 5
    now_rounded = now.replace(minute=minute, second=0, microsecond=0)
    start_at = now_rounded - timedelta(hours=hours_ago)
    end_at = start_at + timedelta(minutes=30)
    app_id = uuid4()
    with Session(engine) as session:
        row = AppointmentModel(
            id=app_id,
            patient_id=patient_id,
            professional_id=professional_id,
            chair_id=chair_id,
            service_id=service_id,
            start_at=start_at,
            end_at=end_at,
            status=status,
            created_at=start_at,
            updated_at=start_at,
        )
        session.add(row)
        c1 = AppointmentStatusChangeModel(
            id=uuid4(),
            appointment_id=app_id,
            from_status=None,
            to_status="reservado",
            changed_by=RECEPTION_ID,
            changed_at=start_at,
            note=None,
        )
        session.add(c1)
        if status != "reservado":
            c2 = AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=app_id,
                from_status="reservado",
                to_status=status,
                changed_by=RECEPTION_ID,
                changed_at=start_at,
                note=None,
            )
            session.add(c2)
        session.commit()
    return app_id



def test_reception_cancels_reserved_appointment(auth_client: TestClient, test_engine: Engine) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    res = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["id"] == str(app_id)
    assert data["status"] == "cancelado"

    with Session(test_engine) as session:
        repo = AppointmentStatusChangeRepository(session)
        changes = repo.list_by_appointment_id(app_id)
        assert len(changes) == 2
        last = changes[-1]
        assert last.from_status is not None
        assert last.from_status.value == "reservado"
        assert last.to_status.value == "cancelado"
        assert last.changed_by == RECEPTION_ID


def test_admin_cancels_confirmed_appointment(auth_client: TestClient, test_engine: Engine) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    admin_headers = token_for(auth_client, "administrador")
    monday = get_future_monday()
    app_id = create_future_appointment(
        auth_client,
        reception_headers,
        monday,
        start_hour=11,
        prof_id=P2_ID,
        chair_id=CHAIR_2_ID,
        pat_id=PATIENT_2_ID,
    )

    with Session(test_engine) as session:
        row = session.get(AppointmentModel, app_id)
        assert row is not None
        row.status = "confirmado"
        session.add(
            AppointmentStatusChangeModel(
                id=uuid4(),
                appointment_id=app_id,
                from_status="reservado",
                to_status="confirmado",
                changed_by=ADMIN_ID,
                changed_at=datetime.now(timezone.utc),
                note=None,
            )
        )
        session.commit()


    res = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=admin_headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "cancelado"

    with Session(test_engine) as session:
        repo = AppointmentStatusChangeRepository(session)
        changes = repo.list_by_appointment_id(app_id)
        assert len(changes) == 3
        last = changes[-1]
        assert last.from_status is not None
        assert last.from_status.value == "confirmado"
        assert last.to_status.value == "cancelado"
        assert last.changed_by == ADMIN_ID


def test_cancel_attended_appointment_returns_422(auth_client: TestClient, test_engine: Engine) -> None:
    admin_headers = token_for(auth_client, "administrador")
    app_id = create_past_appointment(test_engine, "atendido", hours_ago=2)

    with Session(test_engine) as session:
        initial_count = len(AppointmentStatusChangeRepository(session).list_by_appointment_id(app_id))

    res = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=admin_headers)
    assert res.status_code == 422, res.text
    violations = res.json()["violations"]
    assert any(v["code"] == "INVALID_TRANSITION" for v in violations)

    with Session(test_engine) as session:
        current_count = len(AppointmentStatusChangeRepository(session).list_by_appointment_id(app_id))
        assert current_count == initial_count


def test_cancel_already_cancelled_appointment_returns_422(auth_client: TestClient, test_engine: Engine) -> None:
    headers = token_for(auth_client, "recepcion")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, headers, monday, start_hour=10)

    res1 = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=headers)
    assert res1.status_code == 200

    with Session(test_engine) as session:
        count_after_cancel = len(AppointmentStatusChangeRepository(session).list_by_appointment_id(app_id))

    res2 = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=headers)
    assert res2.status_code == 422, res2.text
    violations = res2.json()["violations"]
    assert any(v["code"] == "INVALID_TRANSITION" for v in violations)

    with Session(test_engine) as session:
        count_after_second = len(AppointmentStatusChangeRepository(session).list_by_appointment_id(app_id))
        assert count_after_second == count_after_cancel


def test_cancel_nonexistent_appointment_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.post(
        "/api/appointments/00000000-0000-0000-0000-000000000999/cancel",
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Turno no encontrado."}


def test_dentist_cannot_cancel_appointment_returns_403(auth_client: TestClient, test_engine: Engine) -> None:
    reception_headers = token_for(auth_client, "recepcion")
    dentist_headers = token_for(auth_client, "odontologo")
    monday = get_future_monday()
    app_id = create_future_appointment(auth_client, reception_headers, monday, prof_id=PROFESSIONAL_ID)

    res = auth_client.post(f"/api/appointments/{app_id}/cancel", headers=dentist_headers)
    assert res.status_code == 403, res.text
    violations = res.json()["violations"]
    assert any(
        v["code"] == "FORBIDDEN_OPERATION" and "No tiene permiso para cancelar turnos." in v["message"]
        for v in violations
    )

    with Session(test_engine) as session:
        row = session.get(AppointmentModel, app_id)
        assert row is not None
        assert row.status == "reservado"
