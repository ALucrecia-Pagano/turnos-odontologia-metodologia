from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.api.errors import NotFoundError
from app.db.models import ProfessionalModel
from app.domain.catalog.result import Ok
from app.domain.model import (
    Appointment,
    AppointmentStatus,
    Block,
    Chair,
    Patient,
    Professional,
    Service,
    WorkingHours,
)
from app.repositories.appointment import AppointmentRepository
from app.repositories.catalog import (
    ChairRepository,
    ProfessionalRepository,
    ServiceRepository,
)
from app.repositories.patients import PatientRepository
from app.services.availability import (
    create_block,
    delete_block,
    get_working_hours,
    list_blocks,
    replace_working_hours,
)

pytestmark = pytest.mark.integration

P1 = UUID("00000000-0000-0000-0000-000000000001")
P_UNKNOWN = UUID("00000000-0000-0000-0000-000000000999")
TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def _setup_entities(session: Session) -> tuple[UUID, UUID, UUID, UUID]:
    prof_id = uuid4()
    patient_id = uuid4()
    chair_id = uuid4()
    service_id = uuid4()

    ProfessionalRepository(session).create(Professional(prof_id, "Dra. Test", True))
    PatientRepository(session).create(Patient(patient_id, "Ana Pérez", "30111222", None, None))
    ChairRepository(session).create(Chair(chair_id, "Sillón 1", True))
    ServiceRepository(session).create(Service(service_id, "Consulta", 30, True))
    session.commit()
    return prof_id, patient_id, chair_id, service_id


def test_get_working_hours_success_and_not_found(connection: Connection) -> None:
    session = Session(bind=connection)
    prof_id, _, _, _ = _setup_entities(session)

    # Inicialmente sin horarios
    hours = get_working_hours(session, prof_id)
    assert hours == ()

    # Profesional inexistente -> NotFoundError
    with pytest.raises(NotFoundError) as exc_info:
        get_working_hours(session, P_UNKNOWN)
    assert exc_info.value.message == "Profesional no encontrado."


def test_replace_working_hours_empty_and_inactive_professional(connection: Connection) -> None:
    session = Session(bind=connection)
    prof_id, _, _, _ = _setup_entities(session)

    now = datetime.now(timezone.utc)
    slots = [WorkingHours(prof_id, 1, 540, 780)]

    # Carga un tramo
    res_hours, outside = replace_working_hours(session, prof_id, slots, now, TZ)
    assert len(res_hours) == 1
    assert outside == []

    # Reemplazo con lista vacía
    res_empty, outside_empty = replace_working_hours(session, prof_id, [], now, TZ)
    assert res_empty == ()
    assert outside_empty == []

    # Profesional inactivo permitido
    prof_model = session.get(ProfessionalModel, prof_id)
    assert prof_model is not None
    prof_model.active = False
    session.commit()

    res_inactive, _ = replace_working_hours(session, prof_id, slots, now, TZ)
    assert len(res_inactive) == 1


def test_replace_working_hours_outside_90_days_window(connection: Connection) -> None:
    session = Session(bind=connection)
    prof_id, pat_id, chair_id, svc_id = _setup_entities(session)

    now = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)
    # Lunes en 10 días (dentro de los 90 días): 2026-11-16 13:00 UTC (10:00 local)
    apt_in_window = Appointment(
        uuid4(),
        pat_id,
        prof_id,
        chair_id,
        svc_id,
        datetime(2026, 11, 16, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 16, 13, 30, tzinfo=timezone.utc),
        AppointmentStatus.RESERVED,
    )
    # Lunes en 100 días (fuera de los 90 días): 2027-02-15 13:00 UTC
    apt_outside_window = Appointment(
        uuid4(),
        pat_id,
        prof_id,
        chair_id,
        svc_id,
        datetime(2027, 2, 15, 13, 0, tzinfo=timezone.utc),
        datetime(2027, 2, 15, 13, 30, tzinfo=timezone.utc),
        AppointmentStatus.RESERVED,
    )
    # Turno cancelado dentro de la ventana
    apt_cancelled = Appointment(
        uuid4(),
        pat_id,
        prof_id,
        chair_id,
        svc_id,
        datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 16, 14, 30, tzinfo=timezone.utc),
        AppointmentStatus.CANCELLED,
    )

    # Persistimos turnos directamente
    from app.db.models import AppointmentModel
    for a in (apt_in_window, apt_outside_window, apt_cancelled):
        session.add(
            AppointmentModel(
                id=a.id,
                patient_id=a.patient_id,
                professional_id=a.professional_id,
                chair_id=a.chair_id,
                service_id=a.service_id,
                start_at=a.start_at,
                end_at=a.end_at,
                status=a.status.value,
                created_at=now,
                updated_at=now,
            )
        )
    session.commit()

    # Horario nuevo: martes (no lunes)
    new_hours = [WorkingHours(prof_id, 2, 540, 780)]
    _, outside = replace_working_hours(session, prof_id, new_hours, now, TZ)

    assert len(outside) == 1
    assert outside[0].id == apt_in_window.id
    assert outside[0].patient_name == "Ana Pérez"
    assert outside[0].status == "reservado"


def test_create_and_delete_block_services(connection: Connection) -> None:
    session = Session(bind=connection)
    prof_id, pat_id, chair_id, svc_id = _setup_entities(session)

    # Creamos un turno reservado
    apt = Appointment(
        uuid4(),
        pat_id,
        prof_id,
        chair_id,
        svc_id,
        datetime(2026, 12, 7, 13, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 13, 30, tzinfo=timezone.utc),
        AppointmentStatus.RESERVED,
    )
    from app.db.models import AppointmentModel
    session.add(
        AppointmentModel(
            id=apt.id,
            patient_id=apt.patient_id,
            professional_id=apt.professional_id,
            chair_id=apt.chair_id,
            service_id=apt.service_id,
            start_at=apt.start_at,
            end_at=apt.end_at,
            status=apt.status.value,
            created_at=apt.start_at,
            updated_at=apt.start_at,
        )
    )
    session.commit()

    # Alta de bloqueo pisando el turno
    block, affected = create_block(
        session,
        prof_id,
        datetime(2026, 12, 7, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 7, 16, 0, tzinfo=timezone.utc),
        "Congreso",
    )
    assert block.professional_id == prof_id
    assert block.reason == "Congreso"
    assert len(affected) == 1
    assert affected[0].id == apt.id
    assert affected[0].patient_name == "Ana Pérez"

    # Listar bloques
    all_blocks = list_blocks(session, prof_id)
    assert len(all_blocks) == 1
    assert all_blocks[0].id == block.id

    # Borrar bloqueo existente
    deleted = delete_block(session, block.id)
    assert deleted.id == block.id
    assert list_blocks(session, prof_id) == ()

    # Borrar inexistente -> NotFoundError
    with pytest.raises(NotFoundError) as exc_info:
        delete_block(session, uuid4())
    assert exc_info.value.message == "Bloqueo no encontrado."
