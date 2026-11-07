"""Apoyo para los tests HTTP de la agenda (C-24): datos demo ficticios y helpers.

Los turnos se crean por POST /api/appointments, las cancelaciones por
POST /api/appointments/{id}/cancel, los bloqueos por POST /api/professionals/{id}/blocks
y los horarios por PUT /api/professionals/{id}/working-hours. Las fechas son relativas
al primer lunes futuro.
"""

from collections.abc import Iterator
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.demo_data import CHAIRS, PATIENTS, PROFESSIONALS, SERVICES
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from tests.integration.auth_support import LOGIN, PASSWORD
from tests.integration.conftest import clean_database_tables

P1_ID = PROFESSIONALS[0].id
P2_ID = PROFESSIONALS[1].id
CHAIR_1_ID = CHAIRS[0].id
CHAIR_2_ID = CHAIRS[1].id
SERVICE_CONTROL_ID = SERVICES[3].id
PATIENT_1_ID = PATIENTS[0].id
PATIENT_2_ID = PATIENTS[1].id
UNKNOWN_ID = UUID("00000000-0000-0000-0000-000000000999")

TZ_BA = ZoneInfo("America/Argentina/Buenos_Aires")


def future_monday() -> date:
    """Primer lunes con al menos 7 días de anticipación (fecha local L)."""
    now = datetime.now(timezone.utc)
    base = now + timedelta(days=7)
    monday = base + timedelta(days=(0 - base.weekday()) % 7)
    return monday.date()


def local_at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=TZ_BA)


def utc_z(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def seed_demo_catalog(engine: Engine) -> None:
    with Session(engine) as session:
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
            if pat_repo.get_by_id(pat.id) is None:
                pat_repo.create(pat)
        session.commit()
    with engine.begin() as conn:
        for professional in PROFESSIONALS:
            conn.execute(
                text("UPDATE professional SET full_name = :name WHERE id = :id"),
                {"name": professional.full_name, "id": professional.id},
            )


def truncate_agenda_tables(engine: Engine) -> None:
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE appointment_status_change DISABLE TRIGGER USER"))
            conn.execute(
                text(
                    "TRUNCATE TABLE appointment_status_change, appointment, block, working_hours CASCADE"
                )
            )
        finally:
            conn.execute(text("ALTER TABLE appointment_status_change ENABLE TRIGGER USER"))


def add_working_hours(
    engine: Engine, professional_id: UUID, weekday: int, start_minute: int, end_minute: int
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO working_hours (id, professional_id, weekday, start_minute, end_minute) "
                "VALUES (:id, :prof, :weekday, :start, :end)"
            ),
            {
                "id": uuid4(),
                "prof": professional_id,
                "weekday": weekday,
                "start": start_minute,
                "end": end_minute,
            },
        )


@pytest.fixture
def agenda_data(test_engine: Engine, auth_app: object) -> Iterator[None]:
    """Datos demo, P1 y P2 con horario del lunes de 09:00 a 13:00; limpieza al final."""
    seed_demo_catalog(test_engine)
    truncate_agenda_tables(test_engine)
    add_working_hours(test_engine, P1_ID, 1, 540, 780)
    add_working_hours(test_engine, P2_ID, 1, 540, 780)
    try:
        yield
    finally:
        clean_database_tables(test_engine)


def book(
    client: TestClient,
    headers: dict[str, str],
    start: datetime,
    *,
    professional_id: UUID = P1_ID,
    chair_id: UUID = CHAIR_1_ID,
    patient_id: UUID = PATIENT_1_ID,
    service_id: UUID = SERVICE_CONTROL_ID,
) -> str:
    res = client.post(
        "/api/appointments",
        json={
            "patientId": str(patient_id),
            "professionalId": str(professional_id),
            "chairId": str(chair_id),
            "serviceId": str(service_id),
            "startAt": start.isoformat(),
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    appointment_id: str = res.json()["id"]
    return appointment_id


def cancel(client: TestClient, headers: dict[str, str], appointment_id: str) -> None:
    res = client.post(f"/api/appointments/{appointment_id}/cancel", headers=headers)
    assert res.status_code == 200, res.text


def add_block(
    client: TestClient,
    professional_id: UUID,
    start: datetime,
    end: datetime,
    reason: str,
) -> str:
    res = client.post(
        f"/api/professionals/{professional_id}/blocks",
        json={"startAt": start.isoformat(), "endAt": end.isoformat(), "reason": reason},
        headers=token_for(client, "administrador"),
    )
    assert res.status_code == 201, res.text
    block_id: str = res.json()["block"]["id"]
    return block_id


def get_agenda(
    client: TestClient, headers: dict[str, str], from_date: date, to_date: date, **extra: str
) -> dict[str, object]:
    res = client.get(
        "/api/agenda",
        params={"from": from_date.isoformat(), "to": to_date.isoformat(), **extra},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body: dict[str, object] = res.json()
    return body


def items(body: dict[str, object], key: str) -> list[dict[str, object]]:
    value = body[key]
    assert isinstance(value, list)
    return [entry for entry in value if isinstance(entry, dict)]


def start_times(body: dict[str, object]) -> list[object]:
    return [entry["startAt"] for entry in items(body, "appointments")]


def only(entries: list[dict[str, object]]) -> dict[str, object]:
    assert len(entries) == 1, entries
    return entries[0]
