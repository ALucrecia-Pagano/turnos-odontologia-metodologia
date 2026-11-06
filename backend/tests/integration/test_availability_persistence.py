from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Connection, insert, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import BlockModel, ProfessionalModel, WorkingHoursModel
from app.db.seed import _seed_catalogs, _seed_patients, _seed_working_hours
from app.demo_data import PROFESSIONALS, WORKING_HOURS
from app.domain.catalog.result import Ok
from app.domain.model import (
    Appointment,
    AppointmentStatus,
    AppointmentReferences,
    Block,
    Chair,
    NewAppointmentRequest,
    Patient,
    Professional,
    ScheduleContext,
    Service,
    WorkingHours,
)
from app.domain.appointment.validate import validate_new_appointment
from app.domain.rules.blocks import check_blocks
from app.domain.violations import Ok as AppointmentOk
from app.domain.violations import ReferenceKind, Rejected, ViolationCode
from app.repositories.blocks import BlockRepository
from app.repositories.catalog import ProfessionalRepository
from app.repositories.working_hours import WorkingHoursRepository

pytestmark = pytest.mark.integration

P1 = PROFESSIONALS[0].id
P2 = PROFESSIONALS[1].id
P3 = PROFESSIONALS[2].id
UNKNOWN = UUID("00000000-0000-0000-0000-000000000999")


class EmptyAppointmentReader:
    def list_for_professional_in_range(
        self, professional_id: UUID, start_at: datetime, end_at: datetime
    ) -> tuple[Appointment, ...]:
        return ()


class FixedAppointmentReader:
    def __init__(self, appointments: tuple[Appointment, ...]) -> None:
        self.appointments = appointments

    def list_for_professional_in_range(
        self, professional_id: UUID, start_at: datetime, end_at: datetime
    ) -> tuple[Appointment, ...]:
        return self.appointments


def _session_with_professional(
    connection: Connection, identifier: UUID = UUID(int=601), active: bool = True
) -> Session:
    session = Session(bind=connection)
    if session.get(ProfessionalModel, identifier) is None:
        result = ProfessionalRepository(session).create(
            Professional(identifier, "Profesional Ficticio", active)
        )
        assert isinstance(result, Ok)
    return session


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostic = getattr(error.orig, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None


def test_working_hours_round_trip_and_order(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = WorkingHoursRepository(session)
    slots = (
        WorkingHours(P1, 3, 540, 1440),
        WorkingHours(P1, 1, 900, 1140),
        WorkingHours(P1, 1, 540, 780),
    )

    result = repository.replace_for_professional(P1, slots)

    assert result == Ok(
        (
            WorkingHours(P1, 1, 540, 780),
            WorkingHours(P1, 1, 900, 1140),
            WorkingHours(P1, 3, 540, 1440),
        )
    )
    assert repository.list_by_professional(P1) == result.entity
    assert repository.list() == result.entity
    assert not hasattr(repository.list()[0], "id")


def test_blocks_round_trip_in_utc_with_and_without_reason(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = BlockRepository(session, EmptyAppointmentReader())
    first = Block(
        UUID("00000000-0000-0000-0000-000000000b01"),
        P1,
        datetime.fromisoformat("2026-11-10T09:00:00-03:00"),
        datetime.fromisoformat("2026-11-10T12:00:00-03:00"),
        "Congreso",
    )
    second = Block(
        UUID("00000000-0000-0000-0000-000000000b02"),
        P1,
        datetime.fromisoformat("2026-11-11T14:00:00-03:00"),
        datetime.fromisoformat("2026-11-11T18:00:00-03:00"),
    )

    assert repository.create(first) == Ok(first)
    assert repository.create(second) == Ok(second)
    assert repository.get_by_id(first.id) == first
    assert repository.list_by_professional(P1) == (first, second)
    assert repository.list() == (first, second)
    assert first.start_at == datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    assert first.end_at == datetime(2026, 11, 10, 15, tzinfo=timezone.utc)
    assert second.reason is None


def test_working_hours_replacement_isolated(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    ProfessionalRepository(session).create(Professional(P2, "Otro Profesional", True))
    repository = WorkingHoursRepository(session)
    monday = WorkingHours(P1, 1, 540, 780)
    tuesday = WorkingHours(P2, 2, 540, 780)
    repository.replace_for_professional(P1, (monday,))
    repository.replace_for_professional(P2, (tuesday,))

    assert repository.replace_for_professional(P1, (WorkingHours(P1, 4, 840, 1080),)) == Ok(
        (WorkingHours(P1, 4, 840, 1080),)
    )
    assert repository.list_by_professional(P1) == (
        WorkingHours(P1, 4, 840, 1080),
    )
    assert repository.list_by_professional(P2) == (tuesday,)


def test_working_hours_replacement_empty_removes_schedule(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = WorkingHoursRepository(session)
    previous = WorkingHours(P1, 1, 540, 780)
    repository.replace_for_professional(P1, (previous,))

    assert repository.replace_for_professional(P1, ()) == Ok(())
    assert repository.list_by_professional(P1) == ()


def test_overlapping_working_hours_rejection_preserves_previous(
    connection: Connection,
) -> None:
    session = _session_with_professional(connection, P1)
    repository = WorkingHoursRepository(session)
    previous = WorkingHours(P1, 1, 540, 780)
    repository.replace_for_professional(P1, (previous,))

    result = repository.replace_for_professional(
        P1,
        (WorkingHours(P1, 2, 540, 780), WorkingHours(P1, 2, 720, 960)),
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is ViolationCode.OVERLAPPING_WORKING_HOURS
    assert repository.list_by_professional(P1) == (previous,)


def test_invalid_working_hours_rejection_preserves_previous(
    connection: Connection,
) -> None:
    session = _session_with_professional(connection, P1)
    repository = WorkingHoursRepository(session)
    previous = WorkingHours(P1, 1, 540, 780)
    repository.replace_for_professional(P1, (previous,))

    result = repository.replace_for_professional(P1, (WorkingHours(P1, 8, 600, 540),))

    assert isinstance(result, Rejected)
    assert result.violations[0].code is ViolationCode.INVALID_WORKING_HOURS
    assert repository.list_by_professional(P1) == (previous,)


def test_invalid_block_rejection_does_not_persist(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = BlockRepository(session, EmptyAppointmentReader())
    candidate = Block(
        UUID("00000000-0000-0000-0000-000000000b03"),
        P1,
        datetime(2026, 11, 12, 15, tzinfo=timezone.utc),
        datetime(2026, 11, 12, 15, tzinfo=timezone.utc),
    )

    result = repository.create(candidate)

    assert isinstance(result, Rejected)
    assert result.violations[0].code is ViolationCode.INVALID_BLOCK
    assert repository.get_by_id(candidate.id) is None


def test_working_hours_weekday_check_rejects_direct_insert(connection: Connection) -> None:
    _session_with_professional(connection, P1)
    statement = insert(WorkingHoursModel).values(
        id=UUID(int=701), professional_id=P1, weekday=0, start_minute=540, end_minute=780
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert _constraint_name(raised.value) == "ck_working_hours_weekday_range"


def test_working_hours_minute_check_rejects_direct_insert(connection: Connection) -> None:
    _session_with_professional(connection, P1)
    statement = insert(WorkingHoursModel).values(
        id=UUID(int=702), professional_id=P1, weekday=1, start_minute=780, end_minute=540
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert _constraint_name(raised.value) == "ck_working_hours_minute_range"


def test_block_interval_check_rejects_direct_insert(connection: Connection) -> None:
    _session_with_professional(connection, P1)
    statement = insert(BlockModel).values(
        id=UUID(int=703),
        professional_id=P1,
        start_at=datetime(2026, 11, 12, 16, tzinfo=timezone.utc),
        end_at=datetime(2026, 11, 12, 15, tzinfo=timezone.utc),
    )

    with pytest.raises(IntegrityError) as raised:
        with connection.begin_nested():
            connection.execute(statement)

    assert _constraint_name(raised.value) == "ck_block_interval_order"


def test_unrelated_block_primary_key_error_is_propagated(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = BlockRepository(session, EmptyAppointmentReader())
    candidate = Block(
        UUID("00000000-0000-0000-0000-000000000b04"),
        P1,
        datetime(2026, 11, 12, 15, tzinfo=timezone.utc),
        datetime(2026, 11, 12, 16, tzinfo=timezone.utc),
    )
    repository.create(candidate)

    with pytest.raises(IntegrityError) as raised:
        repository.create(candidate)

    assert _constraint_name(raised.value) == "pk_block"


def test_unknown_professional_working_hours_with_slots_is_rejected(
    connection: Connection,
) -> None:
    session = Session(bind=connection)
    result = WorkingHoursRepository(session).replace_for_professional(
        UNKNOWN, (WorkingHours(UNKNOWN, 1, 540, 780),)
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].code is ViolationCode.UNKNOWN_REFERENCE
    assert result.violations[0].reference_kind is ReferenceKind.PROFESSIONAL
    assert result.violations[0].message == (
        "El profesional indicado no existe (id "
        "00000000-0000-0000-0000-000000000999)."
    )


def test_unknown_professional_working_hours_empty_is_rejected(
    connection: Connection,
) -> None:
    result = WorkingHoursRepository(Session(bind=connection)).replace_for_professional(
        UNKNOWN, ()
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].message == (
        "El profesional indicado no existe (id "
        "00000000-0000-0000-0000-000000000999)."
    )


def test_unknown_professional_block_is_rejected(connection: Connection) -> None:
    candidate = Block(
        UUID("00000000-0000-0000-0000-000000000b05"),
        UNKNOWN,
        datetime(2026, 11, 12, 15, tzinfo=timezone.utc),
        datetime(2026, 11, 12, 16, tzinfo=timezone.utc),
    )
    result = BlockRepository(Session(bind=connection), EmptyAppointmentReader()).create(
        candidate
    )

    assert isinstance(result, Rejected)
    assert result.violations[0].reference_kind is ReferenceKind.PROFESSIONAL
    assert result.violations[0].message == (
        "El profesional indicado no existe (id "
        "00000000-0000-0000-0000-000000000999)."
    )


def test_inactive_professional_can_save_availability(connection: Connection) -> None:
    session = _session_with_professional(connection, P3, active=False)
    hours = WorkingHoursRepository(session)
    blocks = BlockRepository(session, EmptyAppointmentReader())
    slot = WorkingHours(P3, 5, 540, 780)
    block = Block(
        UUID("00000000-0000-0000-0000-000000000b06"),
        P3,
        datetime(2026, 11, 13, 12, tzinfo=timezone.utc),
        datetime(2026, 11, 13, 14, tzinfo=timezone.utc),
    )

    assert hours.replace_for_professional(P3, (slot,)) == Ok((slot,))
    assert blocks.create(block) == Ok(block)


def test_delete_block_returns_it_and_releases_schedule(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    repository = BlockRepository(session, EmptyAppointmentReader())
    block = Block(
        UUID("00000000-0000-0000-0000-000000000b07"),
        P1,
        datetime(2026, 11, 16, 13, tzinfo=timezone.utc),
        datetime(2026, 11, 16, 14, tzinfo=timezone.utc),
    )
    repository.create(block)
    professional = Professional(P1, "Profesional", True)
    chair = Chair(UUID(int=820), "Sillón", True)
    service = Service(UUID(int=821), "Control", 30)
    request = NewAppointmentRequest(
        UUID(int=822),
        UUID(int=823),
        P1,
        chair.id,
        service.id,
        datetime(2026, 11, 16, 13, tzinfo=timezone.utc),
        changed_by=UUID(int=824),
    )
    references = AppointmentReferences(
        Patient(UUID(int=823), "Paciente", "40111222"),
        professional,
        chair,
        service,
    )
    context = ScheduleContext(
        ZoneInfo("America/Argentina/Buenos_Aires"),
        (WorkingHours(P1, 1, 540, 780),),
        (block,),
        datetime(2026, 11, 15, 12, tzinfo=timezone.utc),
    )
    deleted = repository.delete(block.id)

    before = validate_new_appointment(request, references, (), context)
    context_without_block = ScheduleContext(
        context.tz, context.working_hours, (), context.now
    )
    after = validate_new_appointment(
        request, references, (), context_without_block
    )
    assert deleted == block
    assert repository.get_by_id(block.id) is None
    assert isinstance(before, Rejected)
    assert before.violations[0].code is ViolationCode.BLOCKED_TIME
    assert isinstance(after, AppointmentOk)


def test_delete_missing_block_returns_none(connection: Connection) -> None:
    repository = BlockRepository(
        Session(bind=connection), EmptyAppointmentReader()
    )

    assert repository.delete(UUID("00000000-0000-0000-0000-000000000b99")) is None


def test_list_affected_appointments_uses_reader_without_mutation(
    connection: Connection,
) -> None:
    session = _session_with_professional(connection, P1)
    appointments = (
        Appointment(
            UUID("00000000-0000-0000-0000-000000000a01"),
            UUID(int=801),
            P1,
            UUID(int=802),
            UUID(int=803),
            datetime(2026, 11, 16, 13, tzinfo=timezone.utc),
            datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc),
            AppointmentStatus.RESERVED,
        ),
        Appointment(
            UUID("00000000-0000-0000-0000-000000000a02"),
            UUID(int=804),
            P1,
            UUID(int=805),
            UUID(int=806),
            datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc),
            datetime(2026, 11, 16, 14, tzinfo=timezone.utc),
            AppointmentStatus.CONFIRMED,
        ),
        Appointment(
            UUID("00000000-0000-0000-0000-000000000a03"),
            UUID(int=807),
            P1,
            UUID(int=808),
            UUID(int=809),
            datetime(2026, 11, 16, 13, tzinfo=timezone.utc),
            datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc),
            AppointmentStatus.CANCELLED,
        ),
    )
    block = Block(
        UUID("00000000-0000-0000-0000-000000000b08"),
        P1,
        datetime(2026, 11, 16, 13, tzinfo=timezone.utc),
        datetime(2026, 11, 16, 15, tzinfo=timezone.utc),
    )
    result = BlockRepository(session, FixedAppointmentReader(appointments)).list_affected_appointments(
        block
    )

    assert result == appointments[:2]
    assert tuple(item.status for item in appointments) == (
        AppointmentStatus.RESERVED,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    )


def test_seed_working_hours_is_idempotent_and_preserves_existing(
    connection: Connection,
) -> None:
    _seed_catalogs(Session(bind=connection))
    _seed_patients(Session(bind=connection))
    repository = WorkingHoursRepository(Session(bind=connection))
    original = tuple(slot for slot in WORKING_HOURS if slot.professional_id == P1)
    assert repository.replace_for_professional(P1, original) == Ok(original)

    first_inserted = _seed_working_hours(Session(bind=connection))
    second_inserted = _seed_working_hours(Session(bind=connection))

    assert first_inserted == 15
    assert second_inserted == 0
    assert repository.list_by_professional(P1) == original
    assert len(repository.list()) == 25
    assert connection.execute(text("SELECT count(*) FROM block")).scalar_one() == 0


def test_block_repository_list_by_professional_in_range(connection: Connection) -> None:
    session = _session_with_professional(connection, P1)
    if session.get(ProfessionalModel, P2) is None:
        ProfessionalRepository(session).create(Professional(P2, "Segundo Profesional", True))
    repo = BlockRepository(session, EmptyAppointmentReader())

    b1 = Block(
        UUID("00000000-0000-0000-0000-000000000b11"),
        P1,
        datetime(2026, 12, 7, 12, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 16, tzinfo=timezone.utc),
        "Congreso A",
    )
    b2 = Block(
        UUID("00000000-0000-0000-0000-000000000b12"),
        P1,
        datetime(2026, 12, 21, 12, tzinfo=timezone.utc),
        datetime(2026, 12, 21, 16, tzinfo=timezone.utc),
        "Congreso B",
    )
    b_other = Block(
        UUID("00000000-0000-0000-0000-000000000b13"),
        P2,
        datetime(2026, 12, 7, 12, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 16, tzinfo=timezone.utc),
    )
    assert isinstance(repo.create(b1), Ok)
    assert isinstance(repo.create(b2), Ok)
    assert isinstance(repo.create(b_other), Ok)

    # 1. Ambos filtros: solapa solo b1
    res = repo.list_by_professional_in_range(
        P1,
        datetime(2026, 12, 7, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 14, 0, tzinfo=timezone.utc),
    )
    assert res == (b1,)

    # 2. Toque de bordes semiabiertos: [16:00, 18:00) no solapa con [12:00, 16:00)
    res_border_after = repo.list_by_professional_in_range(
        P1,
        datetime(2026, 12, 7, 16, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 18, tzinfo=timezone.utc),
    )
    assert res_border_after == ()

    # [10:00, 12:00) no solapa con [12:00, 16:00)
    res_border_before = repo.list_by_professional_in_range(
        P1,
        datetime(2026, 12, 7, 10, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 12, tzinfo=timezone.utc),
    )
    assert res_border_before == ()

    # 3. Solo start_at (to abierto): solapa b2
    res_only_from = repo.list_by_professional_in_range(
        P1,
        start_at=datetime(2026, 12, 14, 0, tzinfo=timezone.utc),
    )
    assert res_only_from == (b2,)

    # 4. Solo end_at (from abierto): solapa b1
    res_only_to = repo.list_by_professional_in_range(
        P1,
        end_at=datetime(2026, 12, 14, 0, tzinfo=timezone.utc),
    )
    assert res_only_to == (b1,)

    # 5. Sin filtros: devuelve ambos ordenados por start_at
    res_all = repo.list_by_professional_in_range(P1)
    assert res_all == (b1, b2)
