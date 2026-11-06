from uuid import UUID

import pytest
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from app.api.errors import DomainRejectedError, NotFoundError
from app.domain.violations import ViolationCode
from app.services.patients import (
    create_patient,
    get_patient,
    list_patients,
    update_patient,
)

pytestmark = pytest.mark.integration


def test_patient_service_crud_lifecycle_and_404(connection: Connection) -> None:
    session = Session(bind=connection)

    # 1. create
    patient = create_patient(
        session,
        "Marcos Paz",
        "31.444.555",
        phone="11445566",
        health_insurance="OSDE",
        auto_commit=False,
    )
    assert patient.full_name == "Marcos Paz"
    assert patient.dni == "31444555"

    # 2. get by id
    fetched = get_patient(session, patient.id)
    assert fetched.full_name == "Marcos Paz"
    assert fetched.dni == "31444555"

    # 3. update conserving own DNI
    updated = update_patient(
        session,
        patient.id,
        "Marcos Paz Modificado",
        "31444555",
        phone="99881122",
        health_insurance="Swiss Medical",
        auto_commit=False,
    )
    assert updated.full_name == "Marcos Paz Modificado"
    assert updated.dni == "31444555"

    # 4. list and search
    found_by_name = list_patients(session, query="Paz")
    assert any(p.id == patient.id for p in found_by_name)

    found_by_dni = list_patients(session, query="3144")
    assert any(p.id == patient.id for p in found_by_dni)

    # 5. 404 on nonexistent
    fake_id = UUID("00000000-0000-0000-0000-ffffffffffff")
    with pytest.raises(NotFoundError) as exc_get:
        get_patient(session, fake_id)
    assert exc_get.value.message == "Paciente no encontrado."

    with pytest.raises(NotFoundError) as exc_upd:
        update_patient(session, fake_id, "Nombre", "31444555", auto_commit=False)
    assert exc_upd.value.message == "Paciente no encontrado."

    # 6. duplicate DNI
    patient2 = create_patient(session, "Otro Paciente", "32.111.222", auto_commit=False)
    with pytest.raises(DomainRejectedError) as exc_dup:
        update_patient(session, patient2.id, "Otro Paciente", "31444555", auto_commit=False)
    assert exc_dup.value.rejected.violations[0].code is ViolationCode.DUPLICATE_DNI
