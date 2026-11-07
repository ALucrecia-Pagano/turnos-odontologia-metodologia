from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, select, text
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
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import (
    ADMIN_ID,
    LOGIN,
    OTHER_PROFESSIONAL_ID,
    PASSWORD,
    PROFESSIONAL_ID,
    RECEPTION_ID,
)

pytestmark = pytest.mark.integration

P1_ID = PROFESSIONALS[0].id
P2_ID = PROFESSIONALS[1].id
CHAIR_1_ID = CHAIRS[0].id
CHAIR_2_ID = CHAIRS[1].id
SERVICE_CONTROL_ID = SERVICES[3].id      # Control: 30 min
SERVICE_EXTRACTION_ID = SERVICES[1].id   # Extracción: 60 min
PATIENT_1_ID = PATIENTS[0].id
PATIENT_2_ID = PATIENTS[1].id

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
        # Horario lunes 09:00 a 13:00 (540 a 780) para P1 y P2
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
        with test_engine.begin() as conn:
            try:
                conn.execute(text("ALTER TABLE appointment_status_change DISABLE TRIGGER USER"))
                conn.execute(
                    text("TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE")
                )
            finally:
                conn.execute(text("ALTER TABLE appointment_status_change ENABLE TRIGGER USER"))


# =============================================================================
# 2.1 Alta autorizada de turnos
# =============================================================================


def test_reception_creates_valid_appointment(
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
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert UUID(data["id"])
    assert data["status"] == "reservado"
    end_dt = start_dt + timedelta(minutes=30)
    expected_end_utc = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert data["endAt"] == expected_end_utc

    with Session(test_engine) as session:
        app_db = session.get(AppointmentModel, UUID(data["id"]))
        assert app_db is not None
        assert app_db.status == "reservado"
        history = (
            session.execute(
                select(AppointmentStatusChangeModel).where(
                    AppointmentStatusChangeModel.appointment_id == app_db.id
                )
            )
            .scalars()
            .all()
        )
        assert len(history) == 1
        assert history[0].from_status is None
        assert history[0].to_status == "reservado"
        assert history[0].changed_by == RECEPTION_ID


def test_admin_creates_valid_appointment(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 11, 0, tzinfo=TZ_BA)
    payload = {
        "patientId": str(PATIENT_2_ID),
        "professionalId": str(P2_ID),
        "chairId": str(CHAIR_2_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    headers = token_for(auth_client, "administrador")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "reservado"
    assert data["professionalId"] == str(P2_ID)


def test_doctor_cannot_create_appointment_forbidden(
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
    headers = token_for(auth_client, "odontologo")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 403, res.text
    violations = res.json().get("violations", [])
    assert len(violations) == 1
    assert violations[0]["code"] == "FORBIDDEN_OPERATION"
    assert violations[0]["message"] == "No tiene permiso para dar turnos."

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_create_appointment_without_token_unauthorized(
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
    res = auth_client.post("/api/appointments", json=payload)
    assert res.status_code == 401, res.text

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


# =============================================================================
# 2.2 Duración y validación del cuerpo
# =============================================================================


def test_explicit_duration_min_overrides_service_default(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),  # default 30 min
        "startAt": start_dt.isoformat(),
        "durationMin": 45,
    }
    headers = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    end_dt = start_dt + timedelta(minutes=45)
    expected_end_utc = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert data["endAt"] == expected_end_utc


def test_default_service_duration_used_when_duration_min_omitted(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_EXTRACTION_ID),  # default 60 min
        "startAt": start_dt.isoformat(),
    }
    headers = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    end_dt = start_dt + timedelta(minutes=60)
    expected_end_utc = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert data["endAt"] == expected_end_utc


def test_start_at_without_timezone_returns_400(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": f"{lundi.strftime('%Y-%m-%d')}T10:00:00",
    }
    headers = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 400, res.text

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_extra_field_in_body_returns_400(
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
        "status": "reservado",
    }
    headers = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 400, res.text

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


# =============================================================================
# 2.3 Conflictos de agenda
# =============================================================================


def test_agenda_conflict_professional_overlap(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    first_payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_first = auth_client.post("/api/appointments", json=first_payload, headers=headers)
    assert res_first.status_code == 201, res_first.text

    second_payload = {
        "patientId": str(PATIENT_2_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_2_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_second = auth_client.post("/api/appointments", json=second_payload, headers=headers)
    assert res_second.status_code == 409, res_second.text
    codes = [v["code"] for v in res_second.json().get("violations", [])]
    assert "PROFESSIONAL_OVERLAP" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 1


def test_agenda_conflict_chair_overlap(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    first_payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_first = auth_client.post("/api/appointments", json=first_payload, headers=headers)
    assert res_first.status_code == 201, res_first.text

    second_payload = {
        "patientId": str(PATIENT_2_ID),
        "professionalId": str(P2_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_second = auth_client.post("/api/appointments", json=second_payload, headers=headers)
    assert res_second.status_code == 409, res_second.text
    codes = [v["code"] for v in res_second.json().get("violations", [])]
    assert "CHAIR_OVERLAP" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 1


def test_agenda_conflict_professional_and_chair_overlap(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    first_payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_first = auth_client.post("/api/appointments", json=first_payload, headers=headers)
    assert res_first.status_code == 201, res_first.text

    second_payload = {
        "patientId": str(PATIENT_2_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res_second = auth_client.post("/api/appointments", json=second_payload, headers=headers)
    assert res_second.status_code == 409, res_second.text
    codes = [v["code"] for v in res_second.json().get("violations", [])]
    assert "PROFESSIONAL_OVERLAP" in codes
    assert "CHAIR_OVERLAP" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 1


def test_agenda_conflict_outside_working_hours(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 18, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P2_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 409, res.text
    codes = [v["code"] for v in res.json().get("violations", [])]
    assert "OUTSIDE_WORKING_HOURS" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_agenda_conflict_blocked_time(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_block = datetime(lundi.year, lundi.month, lundi.day, 9, 0, tzinfo=TZ_BA)
    end_block = datetime(lundi.year, lundi.month, lundi.day, 13, 0, tzinfo=TZ_BA)

    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=uuid4(),
                professional_id=P1_ID,
                start_at=start_block,
                end_at=end_block,
                reason="Capacitación",
            )
        )
        session.commit()

    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 409, res.text
    codes = [v["code"] for v in res.json().get("violations", [])]
    assert "BLOCKED_TIME" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


# =============================================================================
# 2.4 Referencias y reglas de validez
# =============================================================================


def test_validity_rule_in_the_past(
    auth_client: TestClient, test_engine: Engine
) -> None:
    now_local = datetime.now(TZ_BA)
    yesterday_local = (now_local - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": yesterday_local.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 422, res.text
    codes = [v["code"] for v in res.json().get("violations", [])]
    assert "IN_THE_PAST" in codes

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_validity_rule_unknown_patient(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": "00000000-0000-0000-0000-0000000000c9",
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 422, res.text
    violations = res.json().get("violations", [])
    assert any(v["code"] == "UNKNOWN_REFERENCE" and v.get("referenceKind") == "PATIENT" for v in violations)

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_validity_rule_two_unknown_references(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": "00000000-0000-0000-0000-0000000000c9",
        "professionalId": str(P1_ID),
        "chairId": "00000000-0000-0000-0000-0000000000b9",
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 422, res.text
    violations = res.json().get("violations", [])
    unknown_kinds = {v.get("referenceKind") for v in violations if v["code"] == "UNKNOWN_REFERENCE"}
    assert "PATIENT" in unknown_kinds
    assert "CHAIR" in unknown_kinds

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


def test_validity_rule_inactive_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    with Session(test_engine) as session:
        ProfessionalRepository(session).deactivate(P2_ID)
        session.commit()

    lundi = get_future_monday()
    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P2_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 422, res.text
    violations = res.json().get("violations", [])
    assert any(v["code"] == "INACTIVE_REFERENCE" and v.get("referenceKind") == "PROFESSIONAL" for v in violations)

    with Session(test_engine) as session:
        assert session.query(AppointmentModel).count() == 0


# =============================================================================
# 2.5 Atomicidad y cableado del alta
# =============================================================================


def test_rejection_leaves_no_appointment_nor_history(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_block = datetime(lundi.year, lundi.month, lundi.day, 9, 0, tzinfo=TZ_BA)
    end_block = datetime(lundi.year, lundi.month, lundi.day, 13, 0, tzinfo=TZ_BA)

    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=uuid4(),
                professional_id=P1_ID,
                start_at=start_block,
                end_at=end_block,
                reason="Bloqueo preventivo",
            )
        )
        session.commit()

    start_dt = datetime(lundi.year, lundi.month, lundi.day, 10, 0, tzinfo=TZ_BA)
    headers = token_for(auth_client, "recepcion")

    payload = {
        "patientId": str(PATIENT_1_ID),
        "professionalId": str(P1_ID),
        "chairId": str(CHAIR_1_ID),
        "serviceId": str(SERVICE_CONTROL_ID),
        "startAt": start_dt.isoformat(),
    }
    res = auth_client.post("/api/appointments", json=payload, headers=headers)
    assert res.status_code == 409, res.text
    codes = [v["code"] for v in res.json().get("violations", [])]
    assert "BLOCKED_TIME" in codes

    with Session(test_engine) as session:
        prof_apps = (
            session.execute(
                select(AppointmentModel).where(AppointmentModel.professional_id == P1_ID)
            )
            .scalars()
            .all()
        )
        assert len(prof_apps) == 0

        total_history = session.query(AppointmentStatusChangeModel).count()
        assert total_history == 0
