from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.models import BlockModel, ChairModel, PatientModel, ServiceModel
from app.domain.model import Chair, Patient, Service
from app.repositories.catalog import ChairRepository, ServiceRepository
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import (
    ADMIN_ID,
    LOGIN,
    OTHER_PROFESSIONAL_ID,
    PASSWORD,
    PROFESSIONAL_ID,
    insert_professional,
)

pytestmark = pytest.mark.integration

UNKNOWN_PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000999")
UNKNOWN_BLOCK_ID = UUID("00000000-0000-0000-0000-000000000b99")
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
def clean_availability_tables(test_engine: Engine, auth_app: object) -> Iterator[None]:
    with Session(test_engine) as session:
        if session.get(PatientModel, PATIENT_ID) is None:
            PatientRepository(session).create(Patient(PATIENT_ID, "Ana Pérez", "30111222", None, None))
        if session.get(ChairModel, CHAIR_ID) is None:
            ChairRepository(session).create(Chair(CHAIR_ID, "Sillón 1", True))
        if session.get(ServiceModel, SERVICE_ID) is None:
            ServiceRepository(session).create(Service(SERVICE_ID, "Consulta", 30, True))
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
                "VALUES (:id, :prof, 1, 540, 1080)"
            ),
            {"id": uuid4(), "prof": PROFESSIONAL_ID},
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


def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


# -----------------------------------------------------------------------------
# 5.1 Listado de bloqueos
# -----------------------------------------------------------------------------


def test_reception_lists_blocks_of_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    b1_start = lundi + timedelta(hours=9)
    b1_end = lundi + timedelta(hours=11)
    b2_start = lundi + timedelta(hours=14)
    b2_end = lundi + timedelta(hours=16)

    with Session(test_engine) as session:
        session.add_all([
            BlockModel(
                id=uuid4(),
                professional_id=PROFESSIONAL_ID,
                start_at=b2_start,
                end_at=b2_end,
                reason="Tarde",
            ),
            BlockModel(
                id=uuid4(),
                professional_id=PROFESSIONAL_ID,
                start_at=b1_start,
                end_at=b1_end,
                reason="Mañana",
            ),
        ])
        session.commit()

    headers = token_for(auth_client, "recepcion")
    res = auth_client.get(f"/api/professionals/{PROFESSIONAL_ID}/blocks", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) == 2
    assert data[0]["reason"] == "Mañana"
    assert data[1]["reason"] == "Tarde"
    assert data[0]["startAt"].endswith("Z")
    assert data[0]["endAt"].endswith("Z")


def test_odontologist_lists_own_blocks(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=uuid4(),
                professional_id=PROFESSIONAL_ID,
                start_at=lundi + timedelta(hours=9),
                end_at=lundi + timedelta(hours=12),
                reason="Propio",
            )
        )
        session.commit()

    headers = token_for(auth_client, "odontologo")
    res = auth_client.get(f"/api/professionals/{PROFESSIONAL_ID}/blocks", headers=headers)
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1


def test_odontologist_lists_other_professional_blocks_forbidden(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = token_for(auth_client, "odontologo")
    res = auth_client.get(f"/api/professionals/{OTHER_PROFESSIONAL_ID}/blocks", headers=headers)
    assert res.status_code == 403, res.text
    violations = res.json().get("violations", [])
    assert len(violations) == 1
    assert violations[0]["code"] == "FORBIDDEN_OPERATION"
    assert violations[0]["message"] == "No tiene permiso para leer bloqueos."


def test_list_blocks_with_from_and_to_filters_overlapping(
    auth_client: TestClient, test_engine: Engine
) -> None:
    dt1_start = datetime(2026, 12, 7, 12, 0, tzinfo=timezone.utc)
    dt1_end = datetime(2026, 12, 7, 16, 0, tzinfo=timezone.utc)
    dt2_start = datetime(2026, 12, 21, 12, 0, tzinfo=timezone.utc)
    dt2_end = datetime(2026, 12, 21, 16, 0, tzinfo=timezone.utc)

    with Session(test_engine) as session:
        session.add_all([
            BlockModel(
                id=uuid4(),
                professional_id=PROFESSIONAL_ID,
                start_at=dt1_start,
                end_at=dt1_end,
                reason="Semana 1",
            ),
            BlockModel(
                id=uuid4(),
                professional_id=PROFESSIONAL_ID,
                start_at=dt2_start,
                end_at=dt2_end,
                reason="Semana 3",
            ),
        ])
        session.commit()

    headers = token_for(auth_client, "administrador")
    url = (
        f"/api/professionals/{PROFESSIONAL_ID}/blocks"
        "?from=2026-12-07T00:00:00-03:00&to=2026-12-14T00:00:00-03:00"
    )
    res = auth_client.get(url, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) == 1
    assert data[0]["reason"] == "Semana 1"


def test_list_blocks_from_without_timezone_returns_400(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    url = f"/api/professionals/{PROFESSIONAL_ID}/blocks?from=2026-12-07T00:00:00"
    res = auth_client.get(url, headers=headers)
    assert res.status_code == 400, res.text


def test_list_blocks_unknown_professional_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.get(f"/api/professionals/{UNKNOWN_PROFESSIONAL_ID}/blocks", headers=headers)
    assert res.status_code == 404, res.text
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


# -----------------------------------------------------------------------------
# 5.2 Alta de bloqueos y turnos afectados
# -----------------------------------------------------------------------------


def test_odontologist_creates_own_block_without_affected_appointments(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_str = (lundi + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (lundi + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "odontologo")
    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str, "reason": "Congreso"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert "block" in data
    block = data["block"]
    assert block["reason"] == "Congreso"
    assert block["professionalId"] == str(PROFESSIONAL_ID)
    assert block["startAt"].endswith("Z")
    assert block["endAt"].endswith("Z")
    assert data["affectedAppointments"] == []


def test_admin_creates_block_for_any_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_str = (lundi + timedelta(hours=14)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (lundi + timedelta(hours=18)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "administrador")
    res = auth_client.post(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str, "reason": "Admin block"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    assert res.json()["block"]["professionalId"] == str(OTHER_PROFESSIONAL_ID)


def test_odontologist_creates_block_for_other_professional_forbidden(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    start_str = (lundi + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (lundi + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "odontologo")
    res = auth_client.post(
        f"/api/professionals/{OTHER_PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str, "reason": "Otro prof"},
        headers=headers,
    )
    assert res.status_code == 403, res.text
    with Session(test_engine) as session:
        count = session.query(BlockModel).filter_by(professional_id=OTHER_PROFESSIONAL_ID).count()
        assert count == 0


def test_reception_creates_block_forbidden(auth_client: TestClient) -> None:
    lundi = get_future_monday()
    start_str = (lundi + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (lundi + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "recepcion")
    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str, "reason": "Recep"},
        headers=headers,
    )
    assert res.status_code == 403, res.text
    violations = res.json().get("violations", [])
    assert len(violations) == 1
    assert violations[0]["code"] == "FORBIDDEN_OPERATION"
    assert violations[0]["message"] == "No tiene permiso para crear bloqueos."


def test_block_start_equal_to_end_returns_422(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    same_str = (lundi + timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "administrador")
    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": same_str, "endAt": same_str, "reason": "Igual"},
        headers=headers,
    )
    assert res.status_code == 422, res.text
    violations = res.json().get("violations", [])
    assert any(v.get("code") == "INVALID_BLOCK" for v in violations)
    with Session(test_engine) as session:
        assert session.query(BlockModel).count() == 0


def test_block_without_timezone_returns_400(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": "2026-12-07T09:00:00", "endAt": "2026-12-07T13:00:00"},
        headers=headers,
    )
    assert res.status_code == 400, res.text


def test_block_unknown_professional_returns_404(auth_client: TestClient) -> None:
    lundi = get_future_monday()
    start_str = (lundi + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (lundi + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    headers = token_for(auth_client, "administrador")
    res = auth_client.post(
        f"/api/professionals/{UNKNOWN_PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str},
        headers=headers,
    )
    assert res.status_code == 404, res.text
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


def test_block_overlapping_reserved_appointment_reports_it_without_canceling(
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
    start_str = (monday + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (monday + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    affected = data["affectedAppointments"]
    assert len(affected) == 1
    assert affected[0]["id"] == str(apt_id)
    assert affected[0]["patientName"] == "Ana Pérez"
    assert affected[0]["status"] == "reservado"

    with Session(test_engine) as session:
        status_in_db = session.execute(
            text("SELECT status FROM appointment WHERE id = :id"), {"id": apt_id}
        ).scalar_one()
        assert status_in_db == "reservado"


def test_block_overlapping_canceled_appointment_not_reported(
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
    start_str = (monday + timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    end_str = (monday + timedelta(hours=13)).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    res = auth_client.post(
        f"/api/professionals/{PROFESSIONAL_ID}/blocks",
        json={"startAt": start_str, "endAt": end_str},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    assert res.json()["affectedAppointments"] == []


# -----------------------------------------------------------------------------
# 5.3 Eliminación de bloqueos
# -----------------------------------------------------------------------------


def test_odontologist_deletes_own_block(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    block_id = uuid4()
    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=block_id,
                professional_id=PROFESSIONAL_ID,
                start_at=lundi + timedelta(hours=9),
                end_at=lundi + timedelta(hours=12),
                reason="Para borrar",
            )
        )
        session.commit()

    headers = token_for(auth_client, "odontologo")
    res = auth_client.delete(f"/api/blocks/{block_id}", headers=headers)
    assert res.status_code == 200, res.text
    deleted = res.json()
    assert deleted["id"] == str(block_id)
    assert deleted["professionalId"] == str(PROFESSIONAL_ID)
    assert deleted["startAt"].endswith("Z")
    assert deleted["endAt"].endswith("Z")

    list_res = auth_client.get(f"/api/professionals/{PROFESSIONAL_ID}/blocks", headers=headers)
    assert all(b["id"] != str(block_id) for b in list_res.json())


def test_admin_deletes_block_of_any_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    block_id = uuid4()
    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=block_id,
                professional_id=OTHER_PROFESSIONAL_ID,
                start_at=lundi + timedelta(hours=9),
                end_at=lundi + timedelta(hours=12),
                reason="Admin borra",
            )
        )
        session.commit()

    headers = token_for(auth_client, "administrador")
    res = auth_client.delete(f"/api/blocks/{block_id}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["id"] == str(block_id)


def test_odontologist_deletes_other_professional_block_forbidden(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    block_id = uuid4()
    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=block_id,
                professional_id=OTHER_PROFESSIONAL_ID,
                start_at=lundi + timedelta(hours=9),
                end_at=lundi + timedelta(hours=12),
                reason="No tocar",
            )
        )
        session.commit()

    headers = token_for(auth_client, "odontologo")
    res = auth_client.delete(f"/api/blocks/{block_id}", headers=headers)
    assert res.status_code == 403, res.text
    with Session(test_engine) as session:
        assert session.get(BlockModel, block_id) is not None


def test_reception_deletes_block_forbidden(
    auth_client: TestClient, test_engine: Engine
) -> None:
    lundi = get_future_monday()
    block_id = uuid4()
    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=block_id,
                professional_id=PROFESSIONAL_ID,
                start_at=lundi + timedelta(hours=9),
                end_at=lundi + timedelta(hours=12),
                reason="Recep delete",
            )
        )
        session.commit()

    headers = token_for(auth_client, "recepcion")
    res = auth_client.delete(f"/api/blocks/{block_id}", headers=headers)
    assert res.status_code == 403, res.text
    with Session(test_engine) as session:
        assert session.get(BlockModel, block_id) is not None


def test_delete_unknown_block_returns_404(auth_client: TestClient) -> None:
    headers = token_for(auth_client, "administrador")
    res = auth_client.delete(f"/api/blocks/{UNKNOWN_BLOCK_ID}", headers=headers)
    assert res.status_code == 404, res.text
    assert res.json() == {"code": "NOT_FOUND", "message": "Bloqueo no encontrado."}


def test_delete_block_frees_schedule(
    auth_client: TestClient, test_engine: Engine
) -> None:
    from zoneinfo import ZoneInfo
    from app.domain.model import NewAppointmentRequest
    from app.domain.violations import Ok
    from app.services.appointments import book_appointment

    monday = get_future_monday()
    block_start = monday.replace(hour=12, minute=0)
    block_end = monday.replace(hour=16, minute=0)
    block_id = uuid4()

    with Session(test_engine) as session:
        session.add(
            BlockModel(
                id=block_id,
                professional_id=PROFESSIONAL_ID,
                start_at=block_start,
                end_at=block_end,
                reason="Bloqueo temporal",
            )
        )
        session.commit()

    headers = token_for(auth_client, "administrador")
    del_res = auth_client.delete(f"/api/blocks/{block_id}", headers=headers)
    assert del_res.status_code == 200, del_res.text

    apt_start = monday.replace(hour=13, minute=0)
    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime.now(timezone.utc)
    req = NewAppointmentRequest(
        id=uuid4(),
        patient_id=PATIENT_ID,
        professional_id=PROFESSIONAL_ID,
        chair_id=CHAIR_ID,
        service_id=SERVICE_ID,
        start_at=apt_start,
        duration_min=30,
        changed_by=ADMIN_ID,
    )
    with Session(test_engine) as session:
        result = book_appointment(session, req, now, tz, auto_commit=True)
        assert isinstance(result, Ok)
