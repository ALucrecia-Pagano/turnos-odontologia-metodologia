from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, Engine, event, text
from sqlalchemy.orm import Session

from app.api.schemas import HistoryEntryResponse, RescheduleDetailResponse
from app.auth.model import AuthenticatedUser
from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
    UserModel,
)
from app.demo_data import CHAIRS, PATIENTS, PROFESSIONALS, SERVICES, USERS
from app.domain.model import Role
from app.repositories.users import UserRepository
from app.services.appointments import get_appointment_history
from tests.integration.conftest import clean_database_tables

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def clean_tables(test_engine: Engine) -> Iterator[None]:
    clean_database_tables(test_engine)
    yield
    clean_database_tables(test_engine)


def _seed_catalogs_and_users(session: Session) -> None:
    for prof in PROFESSIONALS:
        if session.get(ProfessionalModel, prof.id) is None:
            session.add(ProfessionalModel(id=prof.id, full_name=prof.full_name, active=prof.active))
    for ch in CHAIRS:
        if session.get(ChairModel, ch.id) is None:
            session.add(ChairModel(id=ch.id, name=ch.name, name_normalized=ch.name.lower(), active=ch.active))
    for s in SERVICES:
        if session.get(ServiceModel, s.id) is None:
            session.add(ServiceModel(id=s.id, name=s.name, name_normalized=s.name.lower(), default_duration_min=s.default_duration_min, active=True))
    for p in PATIENTS:
        if session.get(PatientModel, p.id) is None:
            session.add(PatientModel(id=p.id, full_name=p.full_name, dni=p.dni))
    user_repo = UserRepository(session)
    for u in USERS:
        if session.get(UserModel, u.id) is None:
            user_repo.create(u, "dummy_hash")
    session.flush()


def test_get_appointment_history_returns_none_if_appointment_not_found(connection: Connection) -> None:
    session = Session(bind=connection)
    _seed_catalogs_and_users(session)
    res = get_appointment_history(session, UUID("00000000-0000-0000-0000-000000000999"))
    assert res is None


def test_get_appointment_history_ascending_order_and_reschedule_mapping(connection: Connection) -> None:
    session = Session(bind=connection)
    _seed_catalogs_and_users(session)

    app_id = uuid4()
    prof1 = PROFESSIONALS[0].id
    prof2 = PROFESSIONALS[1].id
    chair1 = CHAIRS[0].id
    chair2 = CHAIRS[1].id
    patient_id = PATIENTS[0].id
    service_id = SERVICES[0].id
    reception_id = USERS[1].id

    dt1 = datetime(2026, 11, 16, 13, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc)
    dt3 = datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc)
    dt4 = datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc)

    appointment_row = AppointmentModel(
        id=app_id,
        patient_id=patient_id,
        professional_id=prof2,
        chair_id=chair2,
        service_id=service_id,
        start_at=dt3,
        end_at=dt4,
        status="reservado",
        created_at=dt1,
        updated_at=dt3,
    )
    session.add(appointment_row)

    # 1. Alta
    change1 = AppointmentStatusChangeModel(
        id=uuid4(),
        appointment_id=app_id,
        from_status=None,
        to_status="reservado",
        changed_by=reception_id,
        changed_at=dt1,
        note=None,
    )
    # 2. Confirmación
    change2 = AppointmentStatusChangeModel(
        id=uuid4(),
        appointment_id=app_id,
        from_status="reservado",
        to_status="confirmado",
        changed_by=reception_id,
        changed_at=dt2,
        note=None,
    )
    # 3. Reprogramación
    change3 = AppointmentStatusChangeModel(
        id=uuid4(),
        appointment_id=app_id,
        from_status="confirmado",
        to_status="reservado",
        changed_by=reception_id,
        changed_at=dt3,
        note=None,
        reschedule_previous_start_at=dt1,
        reschedule_previous_end_at=dt2,
        reschedule_new_start_at=dt3,
        reschedule_new_end_at=dt4,
        reschedule_previous_professional_id=prof1,
        reschedule_new_professional_id=prof2,
        reschedule_previous_chair_id=chair1,
        reschedule_new_chair_id=chair2,
    )
    session.add_all([change1, change2, change3])
    session.flush()

    user_queries: list[str] = []

    def before_cursor_execute(conn: Any, cursor: Any, statement: str, params: Any, context: Any, executemany: bool) -> None:
        if "app_user" in statement:
            user_queries.append(statement)

    event.listen(connection.engine, "before_cursor_execute", before_cursor_execute)
    try:
        history = get_appointment_history(session, app_id)
    finally:
        event.remove(connection.engine, "before_cursor_execute", before_cursor_execute)

    assert history is not None
    assert len(history) == 3
    # Single query to resolve display names
    assert len(user_queries) == 1

    # Entry 1: Alta
    assert history[0].from_status is None
    assert history[0].to_status == "reservado"
    assert history[0].changed_by == reception_id
    assert history[0].changed_by_name == "Recepción Demo"
    assert history[0].changed_at == "2026-11-16T13:00:00Z"
    assert history[0].reschedule is None

    # Entry 2: Confirmado
    assert history[1].from_status == "reservado"
    assert history[1].to_status == "confirmado"
    assert history[1].changed_by == reception_id
    assert history[1].changed_by_name == "Recepción Demo"
    assert history[1].changed_at == "2026-11-16T13:30:00Z"
    assert history[1].reschedule is None

    # Entry 3: Reprogramado
    assert history[2].from_status == "confirmado"
    assert history[2].to_status == "reservado"
    assert history[2].changed_by == reception_id
    assert history[2].changed_by_name == "Recepción Demo"
    assert history[2].changed_at == "2026-11-16T14:00:00Z"
    res = history[2].reschedule
    assert res is not None
    assert res.previous_start_at == "2026-11-16T13:00:00Z"
    assert res.previous_end_at == "2026-11-16T13:30:00Z"
    assert res.new_start_at == "2026-11-16T14:00:00Z"
    assert res.new_end_at == "2026-11-16T14:30:00Z"
    assert res.previous_professional_id == prof1
    assert res.new_professional_id == prof2
    assert res.previous_chair_id == chair1
    assert res.new_chair_id == chair2


def test_get_appointment_history_unknown_user_leaves_changed_by_name_null(connection: Connection) -> None:
    session = Session(bind=connection)
    _seed_catalogs_and_users(session)

    app_id = uuid4()
    patient_id = PATIENTS[0].id
    prof_id = PROFESSIONALS[0].id
    chair_id = CHAIRS[0].id
    service_id = SERVICES[0].id
    unknown_user_id = UUID("00000000-0000-0000-0000-000000000888")

    dt = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)
    appointment_row = AppointmentModel(
        id=app_id,
        patient_id=patient_id,
        professional_id=prof_id,
        chair_id=chair_id,
        service_id=service_id,
        start_at=dt,
        end_at=datetime(2026, 11, 16, 10, 30, tzinfo=timezone.utc),
        status="reservado",
        created_at=dt,
        updated_at=dt,
    )
    session.add(appointment_row)

    change = AppointmentStatusChangeModel(
        id=uuid4(),
        appointment_id=app_id,
        from_status=None,
        to_status="reservado",
        changed_by=unknown_user_id,
        changed_at=dt,
        note=None,
    )
    session.add(change)
    session.flush()

    history = get_appointment_history(session, app_id)
    assert history is not None
    assert len(history) == 1
    assert history[0].changed_by == unknown_user_id
    assert history[0].changed_by_name is None

