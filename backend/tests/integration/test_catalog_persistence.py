from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.domain.catalog.result import Ok
from app.domain.model import Chair, Patient, Professional, Service
from app.domain.violations import Rejected

pytestmark = pytest.mark.integration


def test_catalog_repositories_round_trip_domain_entities(
    connection: Connection,
) -> None:
    from app.repositories.catalog import ChairRepository, ProfessionalRepository, ServiceRepository
    from app.repositories.patients import PatientRepository

    session = Session(bind=connection)
    professional = ProfessionalRepository(session)
    chair = ChairRepository(session)
    service = ServiceRepository(session)
    patient = PatientRepository(session)

    assert professional.create(Professional(UUID(int=101), "Dra. Test", True)).__class__ is Ok
    assert chair.create(Chair(UUID(int=102), "Sillón Test", True)).__class__ is Ok
    assert service.create(Service(UUID(int=103), "Servicio Test", 45)).__class__ is Ok
    created = patient.create(Patient(UUID(int=104), "Paciente Test", "40.111.222"))
    assert created == Ok(Patient(UUID(int=104), "Paciente Test", "40111222"))
    assert professional.get_by_id(UUID(int=101)) == Professional(
        UUID(int=101), "Dra. Test", True
    )
    assert chair.list() == [Chair(UUID(int=102), "Sillón Test", True)]
    assert service.list() == [Service(UUID(int=103), "Servicio Test", 45, True)]
    assert patient.list() == [Patient(UUID(int=104), "Paciente Test", "40111222")]


def test_catalog_duplicate_names_and_dni_return_domain_rejections(
    connection: Connection,
) -> None:
    from app.repositories.catalog import ChairRepository
    from app.repositories.patients import PatientRepository
    from app.domain.violations import ViolationCode

    session = Session(bind=connection)
    chairs = ChairRepository(session)
    patients = PatientRepository(session)
    chairs.create(Chair(UUID(int=201), "Sillón 1", True))
    duplicate_chair = chairs.create(Chair(UUID(int=202), "  SILLÓN   1  ", True))
    duplicate_patient = patients.create(Patient(UUID(int=203), "Uno", "40.111.222"))
    duplicate_patient_2 = patients.create(Patient(UUID(int=204), "Dos", "40.111.222"))
    assert isinstance(duplicate_chair, Rejected)
    assert duplicate_chair.violations[0].code is ViolationCode.DUPLICATE_NAME
    assert duplicate_patient.__class__ is Ok
    assert isinstance(duplicate_patient_2, Rejected)
    assert duplicate_patient_2.violations[0].code is ViolationCode.DUPLICATE_DNI
    assert connection.execute(text("SELECT count(*) FROM chair")).scalar_one() == 1
    assert connection.execute(text("SELECT count(*) FROM patient")).scalar_one() == 1


def test_catalog_activation_is_idempotent(connection: Connection) -> None:
    from app.repositories.catalog import ProfessionalRepository

    session = Session(bind=connection)
    repository = ProfessionalRepository(session)
    identifier = UUID(int=301)
    repository.create(Professional(identifier, "Dra. Estado", True))
    repository.deactivate(identifier)
    repository.deactivate(identifier)
    repository.reactivate(identifier)
    repository.reactivate(identifier)
    assert repository.get_by_id(identifier) == Professional(identifier, "Dra. Estado", True)


def test_migration_has_catalog_tables_and_is_reversible(
    connection: Connection, test_engine: Engine, test_database_url: URL
) -> None:
    from alembic import command
    from tests.integration.conftest import migration_config

    config = migration_config(test_database_url.render_as_string(hide_password=False))
    command.upgrade(config, "head")
    assert {
        "professional",
        "chair",
        "service",
        "patient",
    }.issubset(set(inspect(connection).get_table_names()))


def test_seed_is_idempotent_and_preserves_fixed_counts(connection: Connection) -> None:
    from app.db.seed import _seed_catalogs, _seed_patients
    from app.repositories.catalog import ChairRepository, ProfessionalRepository, ServiceRepository
    from app.repositories.patients import PatientRepository

    connection.execute(text("DELETE FROM patient"))
    connection.execute(text("DELETE FROM service"))
    connection.execute(text("DELETE FROM chair"))
    connection.execute(text("DELETE FROM professional"))
    session = Session(bind=connection)
    _seed_catalogs(session)
    _seed_patients(session)
    first = {
        "professional": len(ProfessionalRepository(session).list()),
        "chair": len(ChairRepository(session).list()),
        "service": len(ServiceRepository(session).list()),
        "patient": len(PatientRepository(session).list()),
    }
    _seed_catalogs(session)
    _seed_patients(session)
    second = {
        "professional": len(ProfessionalRepository(session).list()),
        "chair": len(ChairRepository(session).list()),
        "service": len(ServiceRepository(session).list()),
        "patient": len(PatientRepository(session).list()),
    }
    assert first == {
        "professional": 3,
        "chair": 3,
        "service": 5,
        "patient": 5,
    }
    assert second == first
