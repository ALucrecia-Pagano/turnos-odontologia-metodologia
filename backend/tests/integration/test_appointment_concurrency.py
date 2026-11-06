from collections.abc import Iterator
from datetime import datetime, timezone
import threading
import time
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, insert, select, text
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
    WorkingHoursModel,
)
from app.domain.model import AppointmentStatus, NewAppointmentRequest
from app.domain.violations import Ok, Rejected, ViolationCode
from app.services.appointments import book_appointment
from tests.integration.conftest import clean_database_tables

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def clean_appointment_tables(test_engine: Engine) -> Iterator[None]:
    clean_database_tables(test_engine)
    yield
    clean_database_tables(test_engine)

P1 = UUID("00000000-0000-0000-0000-000000000001")
P2 = UUID("00000000-0000-0000-0000-000000000002")
C1 = UUID("00000000-0000-0000-0000-0000000000b1")
C2 = UUID("00000000-0000-0000-0000-0000000000b2")
S1 = UUID("00000000-0000-0000-0000-0000000000d4")
PAT1 = UUID("00000000-0000-0000-0000-0000000000c1")
PAT2 = UUID("00000000-0000-0000-0000-0000000000c2")
USER1 = UUID("00000000-0000-0000-0000-000000000099")


def _setup_resources(engine: Engine) -> None:
    with engine.begin() as conn:
        session = Session(bind=conn)
        if session.get(ProfessionalModel, P1) is None:
            session.add(ProfessionalModel(id=P1, full_name="Dra. Uno", active=True))
        if session.get(ProfessionalModel, P2) is None:
            session.add(ProfessionalModel(id=P2, full_name="Dr. Dos", active=True))
        if session.get(ChairModel, C1) is None:
            session.add(ChairModel(id=C1, name="Sillón 1", name_normalized="sillon 1", active=True))
        if session.get(ChairModel, C2) is None:
            session.add(ChairModel(id=C2, name="Sillón 2", name_normalized="sillon 2", active=True))
        if session.get(ServiceModel, S1) is None:
            session.add(
                ServiceModel(
                    id=S1,
                    name="Consulta",
                    name_normalized="consulta",
                    default_duration_min=30,
                    active=True,
                )
            )
        if session.get(PatientModel, PAT1) is None:
            session.add(PatientModel(id=PAT1, full_name="Paciente Uno", dni="12345678"))
        if session.get(PatientModel, PAT2) is None:
            session.add(PatientModel(id=PAT2, full_name="Paciente Dos", dni="87654321"))

        for prof in (P1, P2):
            if session.scalars(select(WorkingHoursModel).where(WorkingHoursModel.professional_id == prof)).first() is None:
                session.add(
                    WorkingHoursModel(
                        id=UUID(f"00000000-0000-0000-0000-0000000000e{1 if prof == P1 else 2}"),
                        professional_id=prof,
                        weekday=1,
                        start_minute=540,
                        end_minute=780,
                    )
                )
        session.flush()


def _wait_for_lock(session_monitor: Session, waiting_pid: int, timeout_sec: float = 2.0) -> bool:
    start = time.monotonic()
    event = threading.Event()
    while time.monotonic() - start < timeout_sec:
        count = session_monitor.scalar(
            text(
                "SELECT count(*) FROM pg_locks "
                "WHERE pid = :pid AND NOT granted"
            ),
            {"pid": waiting_pid},
        )
        if count and count > 0:
            return True
        event.wait(0.02)
    return False


def test_concurrent_booking_same_professional_serialized(test_engine: Engine) -> None:
    _setup_resources(test_engine)

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    app1_id = UUID("00000000-0000-0000-0000-000000000a01")
    app2_id = UUID("00000000-0000-0000-0000-000000000a02")

    req_a = NewAppointmentRequest(
        id=app1_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )
    req_b = NewAppointmentRequest(
        id=app2_id,
        patient_id=PAT2,
        professional_id=P1,  # Mismo profesional P1
        chair_id=C2,        # Distinto sillón C2
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )

    result_b: list[object] = []
    pid_b_holder: list[int] = []
    b_ready = threading.Event()

    def run_b() -> None:
        with Session(bind=test_engine) as session_b:
            session_b.execute(text("SET lock_timeout = '5s'"))
            pid_b = session_b.scalar(text("SELECT pg_backend_pid()"))
            assert pid_b is not None
            pid_b_holder.append(pid_b)
            b_ready.set()
            res = book_appointment(session_b, req_b, now, tz, auto_commit=True)
            result_b.append(res)

    with Session(bind=test_engine) as session_a:
        session_a.execute(text("SET lock_timeout = '5s'"))
        # Conexión A toma el lock sobre P1 y C1 sin commitear (auto_commit=False)
        res_a = book_appointment(session_a, req_a, now, tz, auto_commit=False)
        assert isinstance(res_a, Ok)

        thread_b = threading.Thread(target=run_b)
        thread_b.start()
        b_ready.wait(timeout=2.0)

        with Session(bind=test_engine) as session_monitor:
            # Comprobar por pg_locks que B quedó esperando el lock retenido por A
            is_waiting = _wait_for_lock(session_monitor, pid_b_holder[0], timeout_sec=2.0)
            assert is_waiting, "La conexión B debía quedar bloqueada esperando en pg_locks"

        # Liberar el lock de A haciendo commit
        session_a.commit()
        thread_b.join(timeout=5.0)

    assert len(result_b) == 1
    res_b = result_b[0]
    assert isinstance(res_b, Rejected)
    assert any(v.code == ViolationCode.PROFESSIONAL_OVERLAP for v in res_b.violations)

    with Session(bind=test_engine) as check_session:
        rows = check_session.scalars(
            select(AppointmentModel).where(
                AppointmentModel.professional_id == P1,
                AppointmentModel.start_at == datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            )
        ).all()
        assert len(rows) == 1
        assert rows[0].id == app1_id


def test_concurrent_booking_same_chair_serialized(test_engine: Engine) -> None:
    _setup_resources(test_engine)

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    app1_id = UUID("00000000-0000-0000-0000-000000000a01")
    app2_id = UUID("00000000-0000-0000-0000-000000000a02")

    req_a = NewAppointmentRequest(
        id=app1_id,
        patient_id=PAT1,
        professional_id=P1,  # P1
        chair_id=C1,        # Mismo sillón C1
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )
    req_b = NewAppointmentRequest(
        id=app2_id,
        patient_id=PAT2,
        professional_id=P2,  # P2 (distinto profesional)
        chair_id=C1,        # Mismo sillón C1
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )

    result_b: list[object] = []
    pid_b_holder: list[int] = []
    b_ready = threading.Event()

    def run_b() -> None:
        with Session(bind=test_engine) as session_b:
            session_b.execute(text("SET lock_timeout = '5s'"))
            pid_b = session_b.scalar(text("SELECT pg_backend_pid()"))
            assert pid_b is not None
            pid_b_holder.append(pid_b)
            b_ready.set()
            res = book_appointment(session_b, req_b, now, tz, auto_commit=True)
            result_b.append(res)

    with Session(bind=test_engine) as session_a:
        session_a.execute(text("SET lock_timeout = '5s'"))
        # Conexión A toma el lock sobre P1 y C1 sin commitear (auto_commit=False)
        res_a = book_appointment(session_a, req_a, now, tz, auto_commit=False)
        assert isinstance(res_a, Ok)

        thread_b = threading.Thread(target=run_b)
        thread_b.start()
        b_ready.wait(timeout=2.0)

        with Session(bind=test_engine) as session_monitor:
            # Comprobar por pg_locks que B quedó esperando el lock sobre C1 retenido por A
            is_waiting = _wait_for_lock(session_monitor, pid_b_holder[0], timeout_sec=2.0)
            assert is_waiting, "La conexión B debía quedar bloqueada esperando el lock de sillón en pg_locks"

        # Liberar el lock de A haciendo commit
        session_a.commit()
        thread_b.join(timeout=5.0)

    assert len(result_b) == 1
    res_b = result_b[0]
    assert isinstance(res_b, Rejected)
    assert any(v.code == ViolationCode.CHAIR_OVERLAP for v in res_b.violations)

    with Session(bind=test_engine) as check_session:
        rows = check_session.scalars(
            select(AppointmentModel).where(
                AppointmentModel.chair_id == C1,
                AppointmentModel.start_at == datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            )
        ).all()
        assert len(rows) == 1
        assert rows[0].id == app1_id


def test_concurrent_transition_same_appointment_serialized(test_engine: Engine) -> None:
    from app.domain.model import Actor, Role
    from app.services.appointments import cancel_appointment, change_appointment_status

    _setup_resources(test_engine)
    app1_id = UUID("00000000-0000-0000-0000-000000000a01")
    created_time = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)

    with test_engine.begin() as conn:
        conn.execute(
            insert(AppointmentModel).values(
                id=app1_id,
                patient_id=PAT1,
                professional_id=P1,
                chair_id=C1,
                service_id=S1,
                start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc),
                status="reservado",
                created_at=created_time,
                updated_at=created_time,
            )
        )

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now_cancel = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    now_confirm = datetime(2026, 11, 6, 10, 5, tzinfo=timezone.utc)
    actor_admin = Actor(user_id=USER1, role=Role.ADMINISTRADOR)
    actor_recep = Actor(user_id=USER1, role=Role.RECEPCION)

    result_b: list[object] = []
    pid_b_holder: list[int] = []
    b_ready = threading.Event()

    def run_b() -> None:
        with Session(bind=test_engine) as session_b:
            session_b.execute(text("SET lock_timeout = '5s'"))
            pid_b = session_b.scalar(text("SELECT pg_backend_pid()"))
            assert pid_b is not None
            pid_b_holder.append(pid_b)
            b_ready.set()
            res = change_appointment_status(
                session_b,
                app1_id,
                AppointmentStatus.CONFIRMED,
                actor_recep,
                now_confirm,
                tz,
                auto_commit=True,
            )
            result_b.append(res)

    with Session(bind=test_engine) as session_a:
        session_a.execute(text("SET lock_timeout = '5s'"))
        # Conexión A cancela el turno pero retiene la transacción sin commit (auto_commit=False)
        res_a = cancel_appointment(
            session_a,
            app1_id,
            actor_admin,
            now_cancel,
            tz,
            auto_commit=False,
        )
        assert isinstance(res_a, Ok)

        thread_b = threading.Thread(target=run_b)
        thread_b.start()
        b_ready.wait(timeout=2.0)

        with Session(bind=test_engine) as session_monitor:
            # Comprobar en pg_locks que B quedó esperando el lock de fila de app1 retenido por A
            is_waiting = _wait_for_lock(session_monitor, pid_b_holder[0], timeout_sec=2.0)
            assert is_waiting, "La conexión B debía quedar bloqueada esperando el lock de fila en pg_locks"

        # Conexión A hace commit liberando el lock
        session_a.commit()
        thread_b.join(timeout=5.0)

    assert len(result_b) == 1
    res_b = result_b[0]
    assert isinstance(res_b, Rejected)
    assert any(v.code == ViolationCode.INVALID_TRANSITION for v in res_b.violations)

    with Session(bind=test_engine) as check_session:
        app_row = check_session.get(AppointmentModel, app1_id)
        assert app_row is not None
        assert app_row.status == "cancelado"

        history = check_session.scalars(
            select(AppointmentStatusChangeModel).where(
                AppointmentStatusChangeModel.appointment_id == app1_id
            )
        ).all()
        # Exactamente una sola entrada de historial nueva: reservado -> cancelado
        assert len(history) == 1
        assert history[0].from_status == "reservado"
        assert history[0].to_status == "cancelado"


