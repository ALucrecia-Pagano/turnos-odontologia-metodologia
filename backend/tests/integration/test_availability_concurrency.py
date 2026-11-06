from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import threading
import time
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    BlockModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
    WorkingHoursModel,
)
from app.domain.model import Block, NewAppointmentRequest
from app.domain.violations import Ok, Rejected, ValidationResult, ViolationCode
from app.services.appointments import book_appointment
from app.services.availability import AffectedAppointment, create_block
from tests.integration.conftest import clean_database_tables

pytestmark = pytest.mark.integration

P1 = UUID("00000000-0000-0000-0000-000000000001")
C1 = UUID("00000000-0000-0000-0000-0000000000b1")
S1 = UUID("00000000-0000-0000-0000-0000000000d1")
PAT1 = UUID("00000000-0000-0000-0000-0000000000c1")
USER1 = UUID("00000000-0000-0000-0000-000000000099")


@pytest.fixture(autouse=True)
def clean_concurrency_tables(test_engine: Engine) -> Iterator[None]:
    clean_database_tables(test_engine)
    yield
    clean_database_tables(test_engine)


def get_future_monday() -> datetime:
    """Calcula el primer lunes que esté al menos 7 días después de hoy (D13)."""
    now = datetime.now(timezone.utc)
    base = now + timedelta(days=7)
    days_ahead = (0 - base.weekday()) % 7
    monday = base + timedelta(days=days_ahead)
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def _setup_resources(engine: Engine) -> None:
    with engine.begin() as conn:
        session = Session(bind=conn)
        if session.get(ProfessionalModel, P1) is None:
            session.add(ProfessionalModel(id=P1, full_name="Dra. Uno", active=True))
        if session.get(ChairModel, C1) is None:
            session.add(ChairModel(id=C1, name="Sillón 1", name_normalized="sillon 1", active=True))
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
            session.add(PatientModel(id=PAT1, full_name="Ana Pérez", dni="12345678"))

        session.add(
            WorkingHoursModel(
                id=uuid4(),
                professional_id=P1,
                weekday=1,
                start_minute=540,
                end_minute=1080,
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


def test_concurrent_block_waiting_for_booking_reports_new_appointment(
    test_engine: Engine,
) -> None:
    _setup_resources(test_engine)

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    monday = get_future_monday()
    # lunes L 10:00 a 10:30 local -> 13:00 a 13:30 UTC
    apt_start = monday.replace(hour=13, minute=0)
    now = datetime.now(timezone.utc)
    apt_id = uuid4()

    req_a = NewAppointmentRequest(
        id=apt_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=apt_start,
        duration_min=30,
        changed_by=USER1,
    )

    # Bloqueo: lunes L 09:00 a 13:00 local -> 12:00 a 16:00 UTC
    block_start = monday.replace(hour=12, minute=0)
    block_end = monday.replace(hour=16, minute=0)

    result_b: list[tuple[Block, list[AffectedAppointment]]] = []
    pid_b_holder: list[int] = []
    b_ready = threading.Event()

    def run_b() -> None:
        with Session(bind=test_engine) as session_b:
            session_b.execute(text("SET lock_timeout = '5s'"))
            pid_b = session_b.scalar(text("SELECT pg_backend_pid()"))
            assert pid_b is not None
            pid_b_holder.append(pid_b)
            b_ready.set()
            res = create_block(
                session=session_b,
                professional_id=P1,
                start_at=block_start,
                end_at=block_end,
                reason="Congreso",
                auto_commit=True,
            )
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
    block, affected = result_b[0]
    assert block.professional_id == P1
    assert any(apt.id == apt_id for apt in affected)

    with Session(bind=test_engine) as check_session:
        saved_block = check_session.get(BlockModel, block.id)
        assert saved_block is not None
        saved_apt = check_session.get(AppointmentModel, apt_id)
        assert saved_apt is not None


def test_concurrent_booking_waiting_for_block_receives_blocked_time(
    test_engine: Engine,
) -> None:
    _setup_resources(test_engine)

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    monday = get_future_monday()
    # Bloqueo A: lunes L 09:00 a 13:00 local -> 12:00 a 16:00 UTC
    block_start = monday.replace(hour=12, minute=0)
    block_end = monday.replace(hour=16, minute=0)

    # Turno B: lunes L 10:00 a 10:30 local -> 13:00 a 13:30 UTC
    apt_start = monday.replace(hour=13, minute=0)
    now = datetime.now(timezone.utc)
    apt_id = uuid4()

    req_b = NewAppointmentRequest(
        id=apt_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=apt_start,
        duration_min=30,
        changed_by=USER1,
    )

    result_b: list[ValidationResult] = []
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
        # Conexión A crea el bloqueo con auto_commit=False, reteniendo el lock
        block_a, affected_a = create_block(
            session=session_a,
            professional_id=P1,
            start_at=block_start,
            end_at=block_end,
            reason="Bloqueo exclusivo",
            auto_commit=False,
        )

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
    assert any(v.code == ViolationCode.BLOCKED_TIME for v in res_b.violations)

    with Session(bind=test_engine) as check_session:
        saved_apt = check_session.get(AppointmentModel, apt_id)
        assert saved_apt is None
