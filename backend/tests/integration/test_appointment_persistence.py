from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    AppointmentModel,
    AppointmentStatusChangeModel,
    ChairModel,
    PatientModel,
    ProfessionalModel,
    ServiceModel,
)
from app.repositories._integrity import constraint_name
from tests.integration.conftest import clean_database_tables

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def clean_appointment_tables(test_engine: Engine) -> Iterator[None]:
    clean_database_tables(test_engine)
    yield
    clean_database_tables(test_engine)


P1 = UUID("00000000-0000-0000-0000-000000000001")
C1 = UUID("00000000-0000-0000-0000-0000000000b1")
S1 = UUID("00000000-0000-0000-0000-0000000000d4")
PAT1 = UUID("00000000-0000-0000-0000-0000000000c1")
USER1 = UUID("00000000-0000-0000-0000-000000000099")
APP1 = UUID("00000000-0000-0000-0000-000000000a01")


def _setup_references(connection: Connection) -> None:
    session = Session(bind=connection)
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
        session.add(PatientModel(id=PAT1, full_name="Paciente Uno", dni="12345678"))
    session.flush()


def test_appointment_status_check_rejects_invalid_direct_insert(connection: Connection) -> None:
    _setup_references(connection)
    statement = insert(AppointmentModel).values(
        id=UUID("00000000-0000-0000-0000-000000000e01"),
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc),
        status="en_espera",
        created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert constraint_name(raised.value) == "ck_appointment_status"


def test_appointment_interval_check_rejects_direct_insert(connection: Connection) -> None:
    _setup_references(connection)
    statement = insert(AppointmentModel).values(
        id=UUID("00000000-0000-0000-0000-000000000e02"),
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 14, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        status="reservado",
        created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert constraint_name(raised.value) == "ck_appointment_interval_order"


def test_appointment_status_change_reschedule_all_or_none_check_rejects_partial(
    connection: Connection,
) -> None:
    _setup_references(connection)
    # Primero insertar un turno válido para FK
    connection.execute(
        insert(AppointmentModel).values(
            id=APP1,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )

    statement = insert(AppointmentStatusChangeModel).values(
        id=UUID("00000000-0000-0000-0000-000000000f01"),
        appointment_id=APP1,
        from_status="reservado",
        to_status="reservado",
        changed_by=USER1,
        changed_at=datetime(2026, 11, 5, 14, 0, tzinfo=timezone.utc),
        reschedule_previous_start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        reschedule_previous_end_at=None,
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert (
        constraint_name(raised.value)
        == "ck_appointment_status_change_reschedule_all_or_none"
    )


def test_appointment_status_change_trigger_rejects_direct_update(
    connection: Connection,
) -> None:
    _setup_references(connection)
    connection.execute(
        insert(AppointmentModel).values(
            id=APP1,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    change_id = UUID("00000000-0000-0000-0000-000000000f02")
    connection.execute(
        insert(AppointmentStatusChangeModel).values(
            id=change_id,
            appointment_id=APP1,
            from_status=None,
            to_status="reservado",
            changed_by=USER1,
            changed_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            note="Inicial",
        )
    )

    # Mutación removida: trigger activo
    with pytest.raises(Exception) as raised:
        with connection.begin_nested():
            connection.execute(
                text(
                    "UPDATE appointment_status_change SET note = 'modificado' WHERE id = :id"
                ),
                {"id": change_id},
            )

    assert "appointment_status_change is append-only" in str(raised.value)


def test_appointment_status_change_trigger_rejects_direct_delete(
    connection: Connection,
) -> None:
    _setup_references(connection)
    connection.execute(
        insert(AppointmentModel).values(
            id=APP1,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    change_id = UUID("00000000-0000-0000-0000-000000000f03")
    connection.execute(
        insert(AppointmentStatusChangeModel).values(
            id=change_id,
            appointment_id=APP1,
            from_status=None,
            to_status="reservado",
            changed_by=USER1,
            changed_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            note="Inicial",
        )
    )

    with pytest.raises(Exception) as raised:
        with connection.begin_nested():
            connection.execute(
                text("DELETE FROM appointment_status_change WHERE id = :id"),
                {"id": change_id},
            )

    assert "appointment_status_change is append-only" in str(raised.value)


def test_appointment_status_change_trigger_rejects_truncate(
    test_engine: Engine,
) -> None:
    with pytest.raises(Exception) as raised:
        with test_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE appointment_status_change"))

    assert "appointment_status_change is append-only" in str(raised.value)


def test_sql_appointment_reader_filters_and_orders_in_range(
    connection: Connection,
) -> None:
    from app.domain.model import Appointment, AppointmentStatus
    from app.repositories.appointment import SqlAppointmentReader

    _setup_references(connection)
    session = Session(bind=connection)
    p2 = UUID("00000000-0000-0000-0000-000000000002")
    if session.get(ProfessionalModel, p2) is None:
        session.add(ProfessionalModel(id=p2, full_name="Dr. Dos", active=True))
        session.flush()

    # 4 turnos:
    # 1. P1 de 10:00 a 11:00 UTC (solapa con 10:30 a 11:30) -> DEBE estar
    # 2. P1 de 12:00 a 13:00 UTC (fuera de rango) -> NO debe estar
    # 3. P2 de 10:30 a 11:00 UTC (otro profesional) -> NO debe estar
    # 4. P1 de 10:15 a 10:45 UTC (solapa con 10:30 a 11:30) -> DEBE estar, después de app1
    app1 = UUID("00000000-0000-0000-0000-000000000a11")
    app2 = UUID("00000000-0000-0000-0000-000000000a12")
    app3 = UUID("00000000-0000-0000-0000-000000000a13")
    app4 = UUID("00000000-0000-0000-0000-000000000a14")

    session.add(
        AppointmentModel(
            id=app1,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 11, 0, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.add(
        AppointmentModel(
            id=app2,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.add(
        AppointmentModel(
            id=app3,
            patient_id=PAT1,
            professional_id=p2,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 10, 30, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 11, 0, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.add(
        AppointmentModel(
            id=app4,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 10, 15, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 10, 45, tzinfo=timezone.utc),
            status="confirmado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.flush()

    reader = SqlAppointmentReader(session)
    results = reader.list_for_professional_in_range(
        P1,
        datetime(2026, 11, 9, 10, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 9, 11, 30, tzinfo=timezone.utc),
    )

    assert len(results) == 2
    assert [r.id for r in results] == [app1, app4]
    assert results[0].start_at == datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)
    assert results[0].status == AppointmentStatus.RESERVED
    assert results[1].start_at == datetime(2026, 11, 9, 10, 15, tzinfo=timezone.utc)
    assert results[1].status == AppointmentStatus.CONFIRMED


def test_block_repository_uses_sql_appointment_reader_with_real_rows(
    connection: Connection,
) -> None:
    from app.domain.model import Block
    from app.repositories.appointment import SqlAppointmentReader
    from app.repositories.blocks import BlockRepository

    _setup_references(connection)
    session = Session(bind=connection)

    # Insertamos 2 turnos para P1:
    # app_in: 10:00 a 11:00 UTC (afectado por bloqueo de 09:30 a 10:30 UTC)
    # app_out: 12:00 a 13:00 UTC (no afectado)
    app_in = UUID("00000000-0000-0000-0000-000000000a21")
    app_out = UUID("00000000-0000-0000-0000-000000000a22")

    session.add(
        AppointmentModel(
            id=app_in,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 11, 0, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.add(
        AppointmentModel(
            id=app_out,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            status="reservado",
            created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
        )
    )
    session.flush()

    reader = SqlAppointmentReader(session)
    block_repository = BlockRepository(session, reader)

    block = Block(
        id=UUID("00000000-0000-0000-0000-000000000b01"),
        professional_id=P1,
        start_at=datetime(2026, 11, 9, 9, 30, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 9, 10, 30, tzinfo=timezone.utc),
        reason="Congreso",
    )

    affected = block_repository.list_affected_appointments(block)
    assert len(affected) == 1
    assert affected[0].id == app_in
    assert affected[0].professional_id == P1


def test_book_appointment_success_persists_appointment_and_initial_history(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.db.models import WorkingHoursModel
    from app.domain.model import AppointmentStatus, NewAppointmentRequest
    from app.domain.violations import Ok
    from app.services.appointments import book_appointment

    with test_engine.begin() as conn:
        _setup_references(conn)
        if conn.scalars(select(WorkingHoursModel).where(WorkingHoursModel.professional_id == P1)).first() is None:
            conn.execute(
                insert(WorkingHoursModel).values(
                    id=UUID("00000000-0000-0000-0000-0000000000e1"),
                    professional_id=P1,
                    weekday=1,
                    start_minute=540,
                    end_minute=780,
                )
            )

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    app_id = UUID("00000000-0000-0000-0000-000000000a01")
    request = NewAppointmentRequest(
        id=app_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )

    with Session(bind=test_engine) as session:
        result = book_appointment(session, request, now, tz, auto_commit=True)
        assert isinstance(result, Ok)
        assert result.appointment.id == app_id
        assert result.status_change.from_status is None
        assert result.status_change.to_status == AppointmentStatus.RESERVED

    # Verificación en base de datos
    with Session(bind=test_engine) as check_session:
        app_row = check_session.get(AppointmentModel, app_id)
        assert app_row is not None
        assert app_row.status == "reservado"
        assert app_row.created_at == now
        assert app_row.updated_at == now

        history_rows = check_session.scalars(
            select(AppointmentStatusChangeModel).where(
                AppointmentStatusChangeModel.appointment_id == app_id
            )
        ).all()
        assert len(history_rows) == 1
        assert history_rows[0].from_status is None
        assert history_rows[0].to_status == "reservado"
        assert history_rows[0].changed_by == USER1
        assert history_rows[0].changed_at == now


def test_book_appointment_rejected_overlap_does_not_persist(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.db.models import WorkingHoursModel
    from app.domain.model import NewAppointmentRequest
    from app.domain.violations import Rejected, ViolationCode
    from app.services.appointments import book_appointment

    with test_engine.begin() as conn:
        _setup_references(conn)
        if conn.scalars(select(WorkingHoursModel).where(WorkingHoursModel.professional_id == P1)).first() is None:
            conn.execute(
                insert(WorkingHoursModel).values(
                    id=UUID("00000000-0000-0000-0000-0000000000e1"),
                    professional_id=P1,
                    weekday=1,
                    start_minute=540,
                    end_minute=780,
                )
            )

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    app1_id = UUID("00000000-0000-0000-0000-000000000a01")
    req1 = NewAppointmentRequest(
        id=app1_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )
    with Session(bind=test_engine) as session1:
        res1 = book_appointment(session1, req1, now, tz, auto_commit=True)
        assert res1.__class__.__name__ == "Ok"

    with Session(bind=test_engine) as session_count:
        initial_app_count = session_count.scalar(select(text("count(*)")).select_from(AppointmentModel))
        initial_hist_count = session_count.scalar(select(text("count(*)")).select_from(AppointmentStatusChangeModel))

    # Solicitud solapada: 13:15 a 13:45 UTC para la misma profesional
    app2_id = UUID("00000000-0000-0000-0000-000000000a02")
    req2 = NewAppointmentRequest(
        id=app2_id,
        patient_id=PAT1,
        professional_id=P1,
        chair_id=C1,
        service_id=S1,
        start_at=datetime(2026, 11, 9, 13, 15, tzinfo=timezone.utc),
        duration_min=30,
        changed_by=USER1,
    )
    with Session(bind=test_engine) as session2:
        res2 = book_appointment(session2, req2, now, tz, auto_commit=True)
        assert isinstance(res2, Rejected)
        assert any(v.code == ViolationCode.PROFESSIONAL_OVERLAP for v in res2.violations)

    with Session(bind=test_engine) as session_check:
        final_app_count = session_check.scalar(select(text("count(*)")).select_from(AppointmentModel))
        final_hist_count = session_check.scalar(select(text("count(*)")).select_from(AppointmentStatusChangeModel))
        assert final_app_count == initial_app_count
        assert final_hist_count == initial_hist_count
        assert session_check.get(AppointmentModel, app2_id) is None



def test_book_appointment_atomic_rollback_on_history_failure(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.db.models import WorkingHoursModel
    from app.domain.model import NewAppointmentRequest
    from app.services.appointments import book_appointment

    with test_engine.begin() as conn:
        _setup_references(conn)
        if conn.scalars(select(WorkingHoursModel).where(WorkingHoursModel.professional_id == P1)).first() is None:
            conn.execute(
                insert(WorkingHoursModel).values(
                    id=UUID("00000000-0000-0000-0000-0000000000e1"),
                    professional_id=P1,
                    weekday=1,
                    start_minute=540,
                    end_minute=780,
                )
            )
        # Crear trigger temporal en la base
        conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION fail_history_for_a02()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.appointment_id = '00000000-0000-0000-0000-000000000a02' THEN
                        RAISE EXCEPTION 'Simulated history failure for a02';
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER tr_fail_history_for_a02
                BEFORE INSERT ON appointment_status_change
                FOR EACH ROW EXECUTE FUNCTION fail_history_for_a02();
                """
            )
        )

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    app2_id = UUID("00000000-0000-0000-0000-000000000a02")

    try:
        req = NewAppointmentRequest(
            id=app2_id,
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            duration_min=30,
            changed_by=USER1,
        )
        with Session(bind=test_engine) as session:
            with pytest.raises(Exception) as raised:
                book_appointment(session, req, now, tz, auto_commit=True)

            assert "Simulated history failure for a02" in str(raised.value)

        # Verificar reversión atómica: ni appointment ni appointment_status_change tienen a02
        with Session(bind=test_engine) as check_session:
            assert check_session.get(AppointmentModel, app2_id) is None
            hist = check_session.scalars(
                select(AppointmentStatusChangeModel).where(
                    AppointmentStatusChangeModel.appointment_id == app2_id
                )
            ).all()
            assert len(hist) == 0
    finally:
        with test_engine.begin() as conn:
            conn.execute(
                text(
                    """
                    DROP TRIGGER IF EXISTS tr_fail_history_for_a02 ON appointment_status_change;
                    DROP FUNCTION IF EXISTS fail_history_for_a02();
                    """
                )
            )


def test_book_appointment_acquires_resource_locks_ordered_by_uuid(
    test_engine: Engine,
) -> None:
    from sqlalchemy import event
    from zoneinfo import ZoneInfo
    from app.db.models import WorkingHoursModel
    from app.domain.model import Actor, NewAppointmentRequest, RescheduleRequest, Role
    from app.domain.violations import Ok
    from app.services.appointments import book_appointment, reschedule_appointment

    p2 = UUID("00000000-0000-0000-0000-000000000002")
    c2 = UUID("00000000-0000-0000-0000-0000000000b2")
    moved_id = UUID("00000000-0000-0000-0000-000000000a04")

    with test_engine.begin() as conn:
        _setup_references(conn)
        if conn.scalars(select(WorkingHoursModel).where(WorkingHoursModel.professional_id == P1)).first() is None:
            conn.execute(
                insert(WorkingHoursModel).values(
                    id=UUID("00000000-0000-0000-0000-0000000000e1"),
                    professional_id=P1,
                    weekday=1,
                    start_minute=540,
                    end_minute=780,
                )
            )
        conn.execute(insert(ProfessionalModel).values(id=p2, full_name="Dr. Dos", active=True))
        conn.execute(
            insert(ChairModel).values(
                id=c2, name="Sillón 2", name_normalized="sillon 2", active=True
            )
        )
        # Turno en los recursos de UUID mayor: al moverlo a P1 y C1, el orden de
        # llegada (p2, P1) difiere del orden por UUID (P1, p2).
        conn.execute(
            insert(AppointmentModel).values(
                id=moved_id,
                patient_id=PAT1,
                professional_id=p2,
                chair_id=c2,
                service_id=S1,
                start_at=datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 11, 9, 15, 30, tzinfo=timezone.utc),
                status="reservado",
                created_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc),
            )
        )

    executed_queries: list[str] = []
    locked_rows: list[tuple[str, list[object]]] = []

    def before_cursor_execute(
        conn: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        if "FOR UPDATE" in statement:
            executed_queries.append(statement)
            if isinstance(parameters, dict):
                locked_rows.append((statement, list(parameters.values())))

    event.listen(test_engine, "before_cursor_execute", before_cursor_execute)
    try:
        tz = ZoneInfo("America/Argentina/Buenos_Aires")
        now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        req = NewAppointmentRequest(
            id=UUID("00000000-0000-0000-0000-000000000a03"),
            patient_id=PAT1,
            professional_id=P1,
            chair_id=C1,
            service_id=S1,
            start_at=datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc),
            duration_min=30,
            changed_by=USER1,
        )
        with Session(bind=test_engine) as session:
            book_appointment(session, req, now, tz, auto_commit=True)

        assert len(executed_queries) == 2
        # Primera query FOR UPDATE debe ser sobre professional
        assert "professional" in executed_queries[0]
        # Segunda query FOR UPDATE debe ser sobre chair
        assert "chair" in executed_queries[1]

        # Con varios recursos, cada tipo se bloquea en orden ascendente de UUID.
        locked_rows.clear()
        actor = Actor(user_id=USER1, role=Role.RECEPCION)
        move = RescheduleRequest(
            start_at=datetime(2026, 11, 9, 14, 0, tzinfo=timezone.utc),
            professional_id=P1,
            chair_id=C1,
            duration_min=30,
        )
        with Session(bind=test_engine) as session:
            moved = reschedule_appointment(
                session, moved_id, move, actor, now, tz, auto_commit=True
            )
        assert isinstance(moved, Ok)

        professional_locks = [
            ids for statement, ids in locked_rows if "FROM professional" in statement
        ]
        chair_locks = [ids for statement, ids in locked_rows if "FROM chair" in statement]
        assert professional_locks == [[P1], [p2]]
        assert chair_locks == [[C1], [c2]]
    finally:
        event.remove(test_engine, "before_cursor_execute", before_cursor_execute)


def test_change_appointment_status_confirmed_updates_status_and_history(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.domain.model import Actor, AppointmentStatus, Role
    from app.domain.violations import Ok
    from app.services.appointments import change_appointment_status

    with test_engine.begin() as conn:
        _setup_references(conn)
        app_id = UUID("00000000-0000-0000-0000-000000000a01")
        created_time = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        conn.execute(
            insert(AppointmentModel).values(
                id=app_id,
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
        conn.execute(
            insert(AppointmentStatusChangeModel).values(
                id=UUID("00000000-0000-0000-0000-000000000f01"),
                appointment_id=app_id,
                from_status=None,
                to_status="reservado",
                changed_by=USER1,
                changed_at=created_time,
            )
        )

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    confirm_time = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    actor = Actor(user_id=USER1, role=Role.RECEPCION)

    with Session(bind=test_engine) as session:
        result = change_appointment_status(
            session,
            app_id,
            AppointmentStatus.CONFIRMED,
            actor,
            confirm_time,
            tz,
            auto_commit=True,
        )
        assert isinstance(result, Ok)
        assert result.appointment.status == AppointmentStatus.CONFIRMED
        assert result.status_change.from_status == AppointmentStatus.RESERVED
        assert result.status_change.to_status == AppointmentStatus.CONFIRMED

    with Session(bind=test_engine) as check_session:
        app_row = check_session.get(AppointmentModel, app_id)
        assert app_row is not None
        assert app_row.status == "confirmado"
        assert app_row.created_at == created_time
        assert app_row.updated_at == confirm_time

        history = check_session.scalars(
            select(AppointmentStatusChangeModel)
            .where(AppointmentStatusChangeModel.appointment_id == app_id)
            .order_by(AppointmentStatusChangeModel.changed_at)
        ).all()
        assert len(history) == 2
        assert history[1].from_status == "reservado"
        assert history[1].to_status == "confirmado"
        assert history[1].changed_by == USER1
        assert history[1].changed_at == confirm_time


def test_cancel_appointment_updates_status_and_history(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.domain.model import Actor, AppointmentStatus, Role
    from app.domain.violations import Ok
    from app.services.appointments import cancel_appointment

    with test_engine.begin() as conn:
        _setup_references(conn)
        app_id = UUID("00000000-0000-0000-0000-000000000a01")
        created_time = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        conn.execute(
            insert(AppointmentModel).values(
                id=app_id,
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
    cancel_time = datetime(2026, 11, 6, 11, 0, tzinfo=timezone.utc)
    actor = Actor(user_id=USER1, role=Role.ADMINISTRADOR)

    with Session(bind=test_engine) as session:
        result = cancel_appointment(
            session,
            app_id,
            actor,
            cancel_time,
            tz,
            auto_commit=True,
        )
        assert isinstance(result, Ok)
        assert result.appointment.status == AppointmentStatus.CANCELLED
        assert result.status_change.from_status == AppointmentStatus.RESERVED
        assert result.status_change.to_status == AppointmentStatus.CANCELLED

    with Session(bind=test_engine) as check_session:
        app_row = check_session.get(AppointmentModel, app_id)
        assert app_row is not None
        assert app_row.status == "cancelado"
        assert app_row.created_at == created_time
        assert app_row.updated_at == cancel_time

        history = check_session.scalars(
            select(AppointmentStatusChangeModel)
            .where(AppointmentStatusChangeModel.appointment_id == app_id)
        ).all()
        assert len(history) == 1
        assert history[0].from_status == "reservado"
        assert history[0].to_status == "cancelado"
        assert history[0].changed_at == cancel_time


def test_status_operations_on_nonexistent_appointment_return_none(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.domain.model import Actor, AppointmentStatus, Role
    from app.services.appointments import cancel_appointment, change_appointment_status

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
    actor = Actor(user_id=USER1, role=Role.RECEPCION)
    nonexistent = UUID("00000000-0000-0000-0000-000000000a99")

    with Session(bind=test_engine) as session:
        res1 = change_appointment_status(
            session,
            nonexistent,
            AppointmentStatus.CONFIRMED,
            actor,
            now,
            tz,
            auto_commit=True,
        )
        assert res1 is None

        res2 = cancel_appointment(
            session,
            nonexistent,
            actor,
            now,
            tz,
            auto_commit=True,
        )
        assert res2 is None


def test_reschedule_appointment_success_persists_eight_detail_columns(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.db.models import WorkingHoursModel
    from app.domain.model import Actor, AppointmentStatus, RescheduleRequest, Role
    from app.domain.violations import Ok
    from app.services.appointments import reschedule_appointment

    p2 = UUID("00000000-0000-0000-0000-000000000002")
    c2 = UUID("00000000-0000-0000-0000-0000000000b2")

    with test_engine.begin() as conn:
        _setup_references(conn)
        session = Session(bind=conn)
        if session.get(ProfessionalModel, p2) is None:
            session.add(ProfessionalModel(id=p2, full_name="Dr. Dos", active=True))
        if session.get(ChairModel, c2) is None:
            session.add(ChairModel(id=c2, name="Sillón 2", name_normalized="sillon 2", active=True))
        session.flush()

        # Horarios para P1 y P2: lunes 540 a 780 (09:00 a 13:00 local = 12:00 a 16:00 UTC)
        for prof in (P1, p2):
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

        app_id = UUID("00000000-0000-0000-0000-000000000a01")
        created_time = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        session.add(
            AppointmentModel(
                id=app_id,
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
        session.flush()

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    reschedule_time = datetime(2026, 11, 5, 14, 0, tzinfo=timezone.utc)
    actor = Actor(user_id=USER1, role=Role.RECEPCION)
    req = RescheduleRequest(
        start_at=datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc),
        professional_id=p2,
        chair_id=c2,
        duration_min=30,
    )

    with Session(bind=test_engine) as session:
        result = reschedule_appointment(
            session,
            app_id,
            req,
            actor,
            reschedule_time,
            tz,
            auto_commit=True,
        )
        assert isinstance(result, Ok)
        assert result.appointment.professional_id == p2
        assert result.appointment.chair_id == c2
        assert result.appointment.start_at == datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)
        assert result.appointment.end_at == datetime(2026, 11, 9, 15, 30, tzinfo=timezone.utc)

    with Session(bind=test_engine) as check_session:
        app_row = check_session.get(AppointmentModel, app_id)
        assert app_row is not None
        assert app_row.professional_id == p2
        assert app_row.chair_id == c2
        assert app_row.start_at == datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)
        assert app_row.end_at == datetime(2026, 11, 9, 15, 30, tzinfo=timezone.utc)
        assert app_row.status == "reservado"
        assert app_row.created_at == created_time
        assert app_row.updated_at == reschedule_time

        history = check_session.scalars(
            select(AppointmentStatusChangeModel)
            .where(AppointmentStatusChangeModel.appointment_id == app_id)
        ).all()
        assert len(history) == 1
        h = history[0]
        assert h.from_status == "reservado"
        assert h.to_status == "reservado"
        assert h.changed_by == USER1
        assert h.changed_at == reschedule_time
        assert h.reschedule_previous_start_at == datetime(2026, 11, 9, 13, 0, tzinfo=timezone.utc)
        assert h.reschedule_previous_end_at == datetime(2026, 11, 9, 13, 30, tzinfo=timezone.utc)
        assert h.reschedule_new_start_at == datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)
        assert h.reschedule_new_end_at == datetime(2026, 11, 9, 15, 30, tzinfo=timezone.utc)
        assert h.reschedule_previous_professional_id == P1
        assert h.reschedule_new_professional_id == p2
        assert h.reschedule_previous_chair_id == C1
        assert h.reschedule_new_chair_id == c2


def test_reschedule_nonexistent_appointment_returns_none(
    test_engine: Engine,
) -> None:
    from zoneinfo import ZoneInfo
    from app.domain.model import Actor, RescheduleRequest, Role
    from app.services.appointments import reschedule_appointment

    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    now = datetime(2026, 11, 5, 14, 0, tzinfo=timezone.utc)
    actor = Actor(user_id=USER1, role=Role.RECEPCION)
    nonexistent = UUID("00000000-0000-0000-0000-000000000a99")
    req = RescheduleRequest(start_at=datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc))

    with Session(bind=test_engine) as session:
        res = reschedule_appointment(
            session,
            nonexistent,
            req,
            actor,
            now,
            tz,
            auto_commit=True,
        )
        assert res is None







