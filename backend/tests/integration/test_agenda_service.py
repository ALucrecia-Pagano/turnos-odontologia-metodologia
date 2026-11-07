from datetime import date, datetime, time, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Connection, event
from sqlalchemy.orm import Session

from app.db.models import WorkingHoursModel
from app.services.agenda import get_agenda, get_agenda_appointment
from tests.integration.agenda_support import (
    MINE,
    Seed,
    add_appointment,
    add_block,
    base_monday,
    seed_catalog,
)

pytestmark = pytest.mark.integration

TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def local_monday() -> date:
    return base_monday().date()


def local(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=TZ)


def add_working_hours(seed: Seed, professional: UUID, start_minute: int, end_minute: int) -> None:
    seed.session.add(
        WorkingHoursModel(
            id=uuid4(),
            professional_id=professional,
            weekday=1,
            start_minute=start_minute,
            end_minute=end_minute,
        )
    )
    seed.session.flush()


def test_get_agenda_maps_appointments_with_names_and_utc_instants(connection: Connection) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    add_appointment(seed, 8001, local(monday, 10), 30, seed.prof_a, seed.chair_a, "confirmado")

    agenda = get_agenda(seed.session, monday, monday, None, None, TZ)

    row = next(a for a in agenda.appointments if a.id == UUID(int=8001))
    assert row.patient_id == seed.patient
    assert row.patient_name == "Paciente Agenda Ficticio"
    assert row.professional_id == seed.prof_a
    assert row.professional_name == "Dra. Agenda Uno"
    assert row.chair_id == seed.chair_a
    assert row.chair_name == "Sillón Agenda A"
    assert row.service_id == seed.service
    assert row.service_name == "Servicio Agenda"
    assert row.status == "confirmado"
    assert row.start_at == local(monday, 10)
    assert row.start_at.utcoffset() is not None
    assert row.end_at - row.start_at == timedelta(minutes=30)


def test_get_agenda_returns_envelope_with_requested_dates_and_timezone(
    connection: Connection,
) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()

    agenda = get_agenda(seed.session, monday, monday + timedelta(days=6), None, None, TZ)

    assert agenda.from_date == monday
    assert agenda.to_date == monday + timedelta(days=6)
    assert agenda.timezone == "America/Argentina/Buenos_Aires"


def test_get_agenda_window_uses_local_midnights_and_inclusive_to(connection: Connection) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    tuesday = monday + timedelta(days=1)
    wednesday = monday + timedelta(days=2)
    # 23:30 a 00:00 locales del lunes: pertenece al lunes.
    add_appointment(seed, 8001, local(monday, 23, 30), 30, seed.prof_a, seed.chair_a)
    # 00:00 a 00:30 locales del martes: pertenece al martes.
    add_appointment(seed, 8002, local(tuesday, 0), 30, seed.prof_a, seed.chair_b)
    # Miércoles al mediodía: fuera de lunes y martes.
    add_appointment(seed, 8003, local(wednesday, 12), 30, seed.prof_b, seed.chair_a)

    only_monday = get_agenda(seed.session, monday, monday, None, None, TZ)
    only_tuesday = get_agenda(seed.session, tuesday, tuesday, None, None, TZ)
    monday_to_tuesday = get_agenda(seed.session, monday, tuesday, None, None, TZ)

    def mine_ids(agenda_ids: list[UUID]) -> list[UUID]:
        return [i for i in agenda_ids if i in MINE]

    assert mine_ids([a.id for a in only_monday.appointments]) == [UUID(int=8001)]
    assert mine_ids([a.id for a in only_tuesday.appointments]) == [UUID(int=8002)]
    assert mine_ids([a.id for a in monday_to_tuesday.appointments]) == [
        UUID(int=8001),
        UUID(int=8002),
    ]


def test_get_agenda_filters_working_hours_and_blocks_by_professional_but_not_by_chair(
    connection: Connection,
) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    add_working_hours(seed, seed.prof_a, 540, 780)
    add_working_hours(seed, seed.prof_b, 900, 1140)
    add_block(seed, 8001, local(monday, 14), local(monday, 15), seed.prof_a)
    add_block(seed, 8002, local(monday, 16), local(monday, 17), seed.prof_b)
    both = {seed.prof_a, seed.prof_b}

    everyone = get_agenda(seed.session, monday, monday, None, None, TZ)
    only_b = get_agenda(seed.session, monday, monday, seed.prof_b, None, TZ)
    chair_filter = get_agenda(seed.session, monday, monday, None, seed.chair_a, TZ)

    assert [(w.professional_id, w.weekday, w.start_minute, w.end_minute)
            for w in everyone.working_hours if w.professional_id in both] == [
        (seed.prof_a, 1, 540, 780),
        (seed.prof_b, 1, 900, 1140),
    ]
    assert [b.id for b in everyone.blocks if b.id in MINE] == [UUID(int=8001), UUID(int=8002)]
    assert {w.professional_id for w in only_b.working_hours} == {seed.prof_b}
    assert [b.id for b in only_b.blocks] == [UUID(int=8002)]
    assert [w.professional_id for w in chair_filter.working_hours if w.professional_id in both] == [
        seed.prof_a,
        seed.prof_b,
    ]
    assert [b.id for b in chair_filter.blocks if b.id in MINE] == [UUID(int=8001), UUID(int=8002)]


def test_get_agenda_applies_professional_and_chair_filters_to_appointments(
    connection: Connection,
) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    add_appointment(seed, 8001, local(monday, 9), 30, seed.prof_a, seed.chair_a)
    add_appointment(seed, 8002, local(monday, 10), 30, seed.prof_a, seed.chair_b)
    add_appointment(seed, 8003, local(monday, 11), 30, seed.prof_b, seed.chair_b)

    by_professional = get_agenda(seed.session, monday, monday, seed.prof_a, None, TZ)
    by_chair = get_agenda(seed.session, monday, monday, None, seed.chair_b, TZ)
    combined = get_agenda(seed.session, monday, monday, seed.prof_a, seed.chair_b, TZ)

    assert [a.id for a in by_professional.appointments] == [UUID(int=8001), UUID(int=8002)]
    assert [a.id for a in by_chair.appointments] == [UUID(int=8002), UUID(int=8003)]
    assert [a.id for a in combined.appointments] == [UUID(int=8002)]


def test_get_agenda_runs_three_queries_without_n_plus_one(connection: Connection) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    for offset in range(5):
        add_appointment(
            seed, 8001 + offset, local(monday, 8 + offset), 30, seed.prof_a, seed.chair_a
        )
    statements: list[str] = []

    def count(conn: object, cursor: object, statement: str, *args: object) -> None:
        statements.append(statement)

    event.listen(connection.engine, "before_cursor_execute", count)
    try:
        agenda = get_agenda(seed.session, monday, monday, None, None, TZ)
    finally:
        event.remove(connection.engine, "before_cursor_execute", count)

    assert len([a for a in agenda.appointments if a.id in MINE]) == 5
    assert len(statements) == 3


def test_get_agenda_does_not_commit_or_rollback(connection: Connection) -> None:
    seed = seed_catalog(connection)
    monday = local_monday()
    events: list[str] = []

    def on_commit(session: Session) -> None:
        events.append("commit")

    def on_rollback(session: Session, previous_transaction: object) -> None:
        events.append("rollback")

    event.listen(seed.session, "after_commit", on_commit)
    event.listen(seed.session, "after_rollback", on_rollback)
    try:
        get_agenda(seed.session, monday, monday, None, None, TZ)
        get_agenda_appointment(seed.session, UUID(int=999999))
    finally:
        event.remove(seed.session, "after_commit", on_commit)
        event.remove(seed.session, "after_rollback", on_rollback)

    assert events == []


def test_get_agenda_appointment_returns_mapped_appointment_or_none(
    connection: Connection,
) -> None:
    seed = seed_catalog(connection)
    start = base_monday() + timedelta(hours=12)
    add_appointment(seed, 8001, start, 45, seed.prof_b, seed.chair_b, "cancelado")

    found = get_agenda_appointment(seed.session, UUID(int=8001))

    assert found is not None
    assert found.id == UUID(int=8001)
    assert found.status == "cancelado"
    assert found.professional_name == "Dr. Agenda Dos"
    assert found.chair_name == "Sillón Agenda B"
    assert found.end_at - found.start_at == timedelta(minutes=45)
    assert get_agenda_appointment(seed.session, UUID(int=999999)) is None
