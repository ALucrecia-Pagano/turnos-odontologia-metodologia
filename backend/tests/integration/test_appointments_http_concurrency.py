from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import threading
from uuid import uuid4
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
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import (
    LOGIN,
    PASSWORD,
    PROFESSIONAL_ID,
)

pytestmark = pytest.mark.integration

P1_ID = PROFESSIONALS[0].id
CHAIR_1_ID = CHAIRS[0].id
SERVICE_CONTROL_ID = SERVICES[3].id
PATIENT_1_ID = PATIENTS[0].id

TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")


def get_future_monday() -> datetime:
    """Calcula el primer lunes que esté al menos 7 días después de hoy (D8/D13)."""
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
def setup_appointment_demo_data(test_engine: Engine, auth_app: object) -> Iterator[None]:
    with Session(test_engine) as session:
        prof_repo = ProfessionalRepository(session)
        for p in PROFESSIONALS:
            existing_p = prof_repo.get_by_id(p.id)
            if existing_p is None:
                prof_repo.create(p)
            elif not existing_p.active and p.active:
                prof_repo.reactivate(p.id)

        chair_repo = ChairRepository(session)
        for c in CHAIRS:
            existing_c = chair_repo.get_by_id(c.id)
            if existing_c is None:
                chair_repo.create(c)
            elif not existing_c.active and c.active:
                chair_repo.reactivate(c.id)

        serv_repo = ServiceRepository(session)
        for s in SERVICES:
            existing_s = serv_repo.get_by_id(s.id)
            if existing_s is None:
                serv_repo.create(s)
            elif not existing_s.active and s.active:
                serv_repo.reactivate(s.id)

        pat_repo = PatientRepository(session)
        for pat in PATIENTS:
            existing_pat = pat_repo.get_by_id(pat.id)
            if existing_pat is None:
                pat_repo.create(pat)

        session.commit()

    with test_engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE appointment_status_change DISABLE TRIGGER USER"))
            conn.execute(
                text("TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE")
            )
        finally:
            conn.execute(text("ALTER TABLE appointment_status_change ENABLE TRIGGER USER"))
        conn.execute(
            text(
                "INSERT INTO working_hours (id, professional_id, weekday, start_minute, end_minute) "
                "VALUES (:id1, :p1, 1, 540, 780)"
            ),
            {"id1": uuid4(), "p1": P1_ID},
        )

    try:
        yield
    finally:
        with test_engine.begin() as conn:
            try:
                conn.execute(text("ALTER TABLE appointment_status_change DISABLE TRIGGER USER"))
                conn.execute(
                    text("TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE")
                )
            finally:
                conn.execute(text("ALTER TABLE appointment_status_change ENABLE TRIGGER USER"))


# =============================================================================
# 3.1 Carrera por HTTP
# =============================================================================


def test_two_concurrent_http_appointments_produce_single_slot(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    headers = token_for(auth_client, "recepcion")

    barrier = threading.Barrier(2)
    results: list[int] = []
    lock = threading.Lock()

    def send_request() -> None:
        try:
            barrier.wait(timeout=5.0)
            res = auth_client.post("/api/appointments", json=payload, headers=headers)
            with lock:
                results.append(res.status_code)
        except Exception as e:
            with lock:
                results.append(-1)

    t1 = threading.Thread(target=send_request)
    t2 = threading.Thread(target=send_request)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert sorted(results) == [201, 409]

    with Session(test_engine) as session:
        appointments = session.query(AppointmentModel).all()
        assert len(appointments) == 1
        history = session.query(AppointmentStatusChangeModel).all()
        assert len(history) == 1
