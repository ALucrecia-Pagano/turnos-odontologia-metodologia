from uuid import UUID

import pytest
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.api.errors import DomainRejectedError, NotFoundError
from app.domain.violations import ViolationCode
from app.services.catalog import (
    create_chair,
    create_professional,
    create_service,
    deactivate_chair,
    deactivate_professional,
    deactivate_service,
    get_chair,
    get_professional,
    get_service,
    list_chairs,
    list_professionals,
    list_services,
    reactivate_chair,
    reactivate_professional,
    reactivate_service,
    update_chair,
    update_professional,
    update_service,
)

pytestmark = pytest.mark.integration


def test_professional_service_crud_lifecycle_and_404(connection: Connection) -> None:
    session = Session(bind=connection)

    # 1. create with license
    prof = create_professional(session, "Dr. Roberto Gomez", license_number="MN 55555", auto_commit=False)
    assert prof.entity.full_name == "Dr. Roberto Gomez"
    assert prof.license_number == "MN 55555"

    # 2. get by id
    fetched = get_professional(session, prof.entity.id)
    assert fetched.entity.full_name == "Dr. Roberto Gomez"
    assert fetched.license_number == "MN 55555"

    # 3. update conserving name and changing license
    updated = update_professional(
        session,
        prof.entity.id,
        "Dr. Roberto Gomez",
        license_number="MN 99999",
        auto_commit=False,
    )
    assert updated.entity.full_name == "Dr. Roberto Gomez"
    assert updated.license_number == "MN 99999"

    # 4. deactivate and reactivate
    deact = deactivate_professional(session, prof.entity.id, auto_commit=False)
    assert deact.entity.active is False
    assert deact.license_number == "MN 99999"

    react = reactivate_professional(session, prof.entity.id, auto_commit=False)
    assert react.entity.active is True

    # 5. list with filter
    all_profs = list_professionals(session)
    assert any(p.entity.id == prof.entity.id for p in all_profs)

    # 6. 404 on nonexistent
    fake_id = UUID("00000000-0000-0000-0000-ffffffffffff")
    with pytest.raises(NotFoundError) as exc_get:
        get_professional(session, fake_id)
    assert exc_get.value.message == "Profesional no encontrado."

    with pytest.raises(NotFoundError) as exc_upd:
        update_professional(session, fake_id, "Nombre", auto_commit=False)
    assert exc_upd.value.message == "Profesional no encontrado."

    with pytest.raises(NotFoundError) as exc_deact:
        deactivate_professional(session, fake_id, auto_commit=False)
    assert exc_deact.value.message == "Profesional no encontrado."

    with pytest.raises(NotFoundError) as exc_react:
        reactivate_professional(session, fake_id, auto_commit=False)
    assert exc_react.value.message == "Profesional no encontrado."

    # 7. domain rejection on empty name
    with pytest.raises(DomainRejectedError) as exc_rej:
        create_professional(session, "", auto_commit=False)
    assert exc_rej.value.rejected.violations[0].code is ViolationCode.EMPTY_NAME


def test_chair_service_crud_lifecycle_and_404(connection: Connection) -> None:
    session = Session(bind=connection)

    # 1. create
    chair = create_chair(session, "Sillón Service 1", auto_commit=False)
    assert chair.name == "Sillón Service 1"
    assert chair.active is True

    # 2. get by id
    fetched = get_chair(session, chair.id)
    assert fetched.name == "Sillón Service 1"

    # 3. update
    updated = update_chair(session, chair.id, "Sillón Service 1 Bis", auto_commit=False)
    assert updated.name == "Sillón Service 1 Bis"

    # 4. deactivate and reactivate (idempotent)
    deact = deactivate_chair(session, chair.id, auto_commit=False)
    assert deact.active is False
    deact2 = deactivate_chair(session, chair.id, auto_commit=False)
    assert deact2.active is False

    react = reactivate_chair(session, chair.id, auto_commit=False)
    assert react.active is True

    # 5. list filter
    active_chairs = list_chairs(session, active=True)
    assert any(c.id == chair.id for c in active_chairs)

    # 6. 404 on nonexistent
    fake_id = UUID("00000000-0000-0000-0000-ffffffffffff")
    with pytest.raises(NotFoundError) as exc_get:
        get_chair(session, fake_id)
    assert exc_get.value.message == "Sillón no encontrado."

    with pytest.raises(NotFoundError) as exc_upd:
        update_chair(session, fake_id, "Nombre", auto_commit=False)
    assert exc_upd.value.message == "Sillón no encontrado."

    with pytest.raises(NotFoundError) as exc_deact:
        deactivate_chair(session, fake_id, auto_commit=False)
    assert exc_deact.value.message == "Sillón no encontrado."

    with pytest.raises(NotFoundError) as exc_react:
        reactivate_chair(session, fake_id, auto_commit=False)
    assert exc_react.value.message == "Sillón no encontrado."

    # 7. domain rejection on duplicate
    chair2 = create_chair(session, "Sillón Service 2", auto_commit=False)
    with pytest.raises(DomainRejectedError) as exc_dup:
        update_chair(session, chair2.id, "Sillón Service 1 Bis", auto_commit=False)
    assert exc_dup.value.rejected.violations[0].code is ViolationCode.DUPLICATE_NAME


def test_service_service_crud_lifecycle_and_404(connection: Connection) -> None:
    session = Session(bind=connection)

    # 1. create
    srv = create_service(session, "Ortodoncia Preventiva", 45, auto_commit=False)
    assert srv.name == "Ortodoncia Preventiva"
    assert srv.default_duration_min == 45
    assert srv.active is True

    # 2. get by id
    fetched = get_service(session, srv.id)
    assert fetched.name == "Ortodoncia Preventiva"

    # 3. update
    updated = update_service(session, srv.id, "Ortodoncia Preventiva Plus", 60, auto_commit=False)
    assert updated.name == "Ortodoncia Preventiva Plus"
    assert updated.default_duration_min == 60

    # 4. deactivate and reactivate
    deact = deactivate_service(session, srv.id, auto_commit=False)
    assert deact.active is False

    react = reactivate_service(session, srv.id, auto_commit=False)
    assert react.active is True

    # 5. list
    all_srvs = list_services(session)
    assert any(s.id == srv.id for s in all_srvs)

    # 6. 404 on nonexistent
    fake_id = UUID("00000000-0000-0000-0000-ffffffffffff")
    with pytest.raises(NotFoundError) as exc_get:
        get_service(session, fake_id)
    assert exc_get.value.message == "Prestación no encontrada."

    with pytest.raises(NotFoundError) as exc_upd:
        update_service(session, fake_id, "Nombre", 30, auto_commit=False)
    assert exc_upd.value.message == "Prestación no encontrada."

    with pytest.raises(NotFoundError) as exc_deact:
        deactivate_service(session, fake_id, auto_commit=False)
    assert exc_deact.value.message == "Prestación no encontrada."

    with pytest.raises(NotFoundError) as exc_react:
        reactivate_service(session, fake_id, auto_commit=False)
    assert exc_react.value.message == "Prestación no encontrada."

    # 7. domain rejection on invalid duration
    with pytest.raises(DomainRejectedError) as exc_dur:
        update_service(session, srv.id, "Ortodoncia Preventiva Plus", 0, auto_commit=False)
    assert exc_dur.value.rejected.violations[0].code is ViolationCode.INVALID_DURATION
