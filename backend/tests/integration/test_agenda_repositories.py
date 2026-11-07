from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import Connection, event

from app.domain.model import AppointmentStatus, Block
from app.repositories.appointment import (
    AppointmentRepository,
    AppointmentWithNames,
    SqlAppointmentReader,
)
from app.repositories.blocks import BlockRepository
from tests.integration.agenda_support import (
    MINE,
    Seed,
    add_appointment,
    add_block,
    base_monday,
    seed_catalog,
)

pytestmark = pytest.mark.integration


def mine(rows: tuple[AppointmentWithNames, ...]) -> list[UUID]:
    return [row.appointment.id for row in rows if row.appointment.id in MINE]


def test_list_for_agenda_in_range_returns_appointments_with_names(connection: Connection) -> None:
    seed = seed_catalog(connection)
    start = base_monday() + timedelta(hours=13)
    add_appointment(seed, 8001, start, 30, seed.prof_a, seed.chair_a, "confirmado")

    rows = AppointmentRepository(seed.session).list_for_agenda_in_range(
        start - timedelta(hours=1), start + timedelta(hours=1)
    )

    row = next(r for r in rows if r.appointment.id == UUID(int=8001))
    assert row.patient_name == "Paciente Agenda Ficticio"
    assert row.professional_name == "Dra. Agenda Uno"
    assert row.chair_name == "Sillón Agenda A"
    assert row.service_name == "Servicio Agenda"
    assert row.appointment.status is AppointmentStatus.CONFIRMED
    assert row.appointment.start_at == start
    assert row.appointment.end_at == start + timedelta(minutes=30)
    assert row.appointment.start_at.tzinfo is not None


def test_list_for_agenda_in_range_uses_half_open_overlap(connection: Connection) -> None:
    seed = seed_catalog(connection)
    window_start = base_monday()
    window_end = window_start + timedelta(days=1)
    # Termina justo al abrir la ventana: queda fuera.
    add_appointment(seed, 8001, window_start - timedelta(minutes=30), 30, seed.prof_a, seed.chair_a)
    # Empieza justo al cerrar la ventana: queda fuera.
    add_appointment(seed, 8002, window_end, 30, seed.prof_a, seed.chair_a)
    # Cruza el inicio: queda dentro.
    add_appointment(seed, 8003, window_start - timedelta(minutes=10), 30, seed.prof_a, seed.chair_b)
    # Empieza justo al abrir: queda dentro.
    add_appointment(seed, 8004, window_start, 30, seed.prof_b, seed.chair_a)
    # Termina justo al cerrar: queda dentro.
    add_appointment(seed, 8005, window_end - timedelta(minutes=30), 30, seed.prof_b, seed.chair_b)

    rows = AppointmentRepository(seed.session).list_for_agenda_in_range(window_start, window_end)

    assert mine(rows) == [UUID(int=8003), UUID(int=8004), UUID(int=8005)]


def test_list_for_agenda_in_range_combines_optional_filters(connection: Connection) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    add_appointment(seed, 8001, day + timedelta(hours=9), 30, seed.prof_a, seed.chair_a)
    add_appointment(seed, 8002, day + timedelta(hours=10), 30, seed.prof_a, seed.chair_b)
    add_appointment(seed, 8003, day + timedelta(hours=9), 30, seed.prof_b, seed.chair_b)
    add_appointment(seed, 8004, day + timedelta(hours=10), 30, seed.prof_b, seed.chair_a)
    repo = AppointmentRepository(seed.session)
    end = day + timedelta(days=1)

    assert mine(repo.list_for_agenda_in_range(day, end)) == [
        UUID(int=8001),
        UUID(int=8003),
        UUID(int=8002),
        UUID(int=8004),
    ]
    assert mine(repo.list_for_agenda_in_range(day, end, professional_id=seed.prof_a)) == [
        UUID(int=8001),
        UUID(int=8002),
    ]
    assert mine(repo.list_for_agenda_in_range(day, end, chair_id=seed.chair_a)) == [
        UUID(int=8001),
        UUID(int=8004),
    ]
    assert mine(
        repo.list_for_agenda_in_range(day, end, professional_id=seed.prof_a, chair_id=seed.chair_b)
    ) == [UUID(int=8002)]
    assert repo.list_for_agenda_in_range(day, end, professional_id=UUID(int=999999)) == ()


def test_list_for_agenda_in_range_orders_by_start_then_id(connection: Connection) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    add_appointment(seed, 8003, day + timedelta(hours=11), 30, seed.prof_a, seed.chair_a)
    add_appointment(seed, 8002, day + timedelta(hours=9), 30, seed.prof_b, seed.chair_b)
    add_appointment(seed, 8001, day + timedelta(hours=9), 30, seed.prof_a, seed.chair_a)

    rows = AppointmentRepository(seed.session).list_for_agenda_in_range(
        day, day + timedelta(days=1)
    )

    assert mine(rows) == [UUID(int=8001), UUID(int=8002), UUID(int=8003)]


def test_list_for_agenda_in_range_runs_a_single_query(connection: Connection) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    for offset in range(5):
        add_appointment(
            seed, 8001 + offset, day + timedelta(hours=9 + offset), 30, seed.prof_a, seed.chair_a
        )
    statements: list[str] = []

    def count(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    event.listen(connection.engine, "before_cursor_execute", count)
    try:
        rows = AppointmentRepository(seed.session).list_for_agenda_in_range(
            day, day + timedelta(days=1)
        )
    finally:
        event.remove(connection.engine, "before_cursor_execute", count)

    assert len(mine(rows)) == 5
    assert len(statements) == 1


def test_get_with_names_returns_enriched_row_or_none(connection: Connection) -> None:
    seed = seed_catalog(connection)
    start = base_monday() + timedelta(hours=9)
    add_appointment(seed, 8001, start, 45, seed.prof_b, seed.chair_b, "cancelado")
    repo = AppointmentRepository(seed.session)

    row = repo.get_with_names(UUID(int=8001))

    assert row is not None
    assert row.appointment.id == UUID(int=8001)
    assert row.appointment.status is AppointmentStatus.CANCELLED
    assert row.professional_name == "Dr. Agenda Dos"
    assert row.chair_name == "Sillón Agenda B"
    assert row.patient_name == "Paciente Agenda Ficticio"
    assert row.service_name == "Servicio Agenda"
    assert repo.get_with_names(UUID(int=999999)) is None


def block_repo(seed: Seed) -> BlockRepository:
    return BlockRepository(seed.session, SqlAppointmentReader(seed.session))


def mine_blocks(blocks: tuple[Block, ...]) -> list[UUID]:
    return [b.id for b in blocks if b.id in MINE]


def test_block_list_in_range_uses_half_open_overlap_and_midnight_crossing(
    connection: Connection,
) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    nxt = day + timedelta(days=1)
    # Termina justo al abrir la ventana: queda fuera.
    add_block(seed, 8001, day - timedelta(hours=2), day, seed.prof_a)
    # Empieza justo al cerrar la ventana: queda fuera.
    add_block(seed, 8002, nxt, nxt + timedelta(hours=1), seed.prof_a)
    # Empieza antes y cruza la medianoche de apertura: queda dentro.
    add_block(seed, 8003, day - timedelta(hours=1), day + timedelta(hours=1), seed.prof_a)
    # Cruza la medianoche de cierre: queda dentro.
    add_block(seed, 8004, nxt - timedelta(hours=1), nxt + timedelta(hours=1), seed.prof_b)

    blocks = block_repo(seed).list_in_range(day, nxt)

    assert mine_blocks(blocks) == [UUID(int=8003), UUID(int=8004)]


def test_block_list_in_range_filters_by_optional_professional(connection: Connection) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    add_block(seed, 8001, day + timedelta(hours=9), day + timedelta(hours=10), seed.prof_a)
    add_block(seed, 8002, day + timedelta(hours=11), day + timedelta(hours=12), seed.prof_b)
    repo = block_repo(seed)
    end = day + timedelta(days=1)

    assert mine_blocks(repo.list_in_range(day, end)) == [UUID(int=8001), UUID(int=8002)]
    assert mine_blocks(repo.list_in_range(day, end, professional_id=seed.prof_b)) == [
        UUID(int=8002)
    ]
    assert repo.list_in_range(day, end, professional_id=UUID(int=999999)) == ()


def test_block_list_in_range_orders_by_start_then_id(connection: Connection) -> None:
    seed = seed_catalog(connection)
    day = base_monday()
    add_block(seed, 8003, day + timedelta(hours=14), day + timedelta(hours=15), seed.prof_a)
    add_block(seed, 8002, day + timedelta(hours=9), day + timedelta(hours=10), seed.prof_b)
    add_block(seed, 8001, day + timedelta(hours=9), day + timedelta(hours=10), seed.prof_a)

    blocks = block_repo(seed).list_in_range(day, day + timedelta(days=1))

    assert mine_blocks(blocks) == [UUID(int=8001), UUID(int=8002), UUID(int=8003)]
