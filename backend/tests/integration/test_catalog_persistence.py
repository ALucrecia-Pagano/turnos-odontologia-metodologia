from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, insert, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.config import load_settings
from app.db.models import BlockModel, ChairModel, PatientModel, WorkingHoursModel
from app.db.seed import seed_database
from app.domain.catalog.result import Ok
from app.domain.model import Chair, Patient, Professional, Service
from app.domain.violations import Rejected, ViolationCode

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
    assert chair.get_by_id(UUID(int=102)) == Chair(
        UUID(int=102), "Sillón Test", True
    )
    assert service.get_by_id(UUID(int=103)) == Service(
        UUID(int=103), "Servicio Test", 45, True
    )
    assert patient.get_by_id(UUID(int=104)) == Patient(
        UUID(int=104), "Paciente Test", "40111222"
    )


def test_catalog_duplicate_names_and_dni_return_domain_rejections(
    connection: Connection,
) -> None:
    from app.repositories.catalog import ChairRepository
    from app.repositories.patients import PatientRepository
    from app.domain.violations import ViolationCode

    session = Session(bind=connection)
    chairs = ChairRepository(session)
    patients = PatientRepository(session)
    chairs.create(Chair(UUID(int=201), "Sillón 901", True))
    duplicate_chair = chairs.create(Chair(UUID(int=202), "  SILLÓN   901  ", True))
    duplicate_patient = patients.create(Patient(UUID(int=203), "Uno", "40.111.222"))
    duplicate_patient_2 = patients.create(Patient(UUID(int=204), "Dos", "40.111.222"))
    assert isinstance(duplicate_chair, Rejected)
    assert duplicate_chair.violations[0].code is ViolationCode.DUPLICATE_NAME
    assert duplicate_patient.__class__ is Ok
    assert isinstance(duplicate_patient_2, Rejected)
    assert duplicate_patient_2.violations[0].code is ViolationCode.DUPLICATE_DNI
    assert chairs.get_by_id(UUID(int=201)) is not None
    assert chairs.get_by_id(UUID(int=202)) is None
    assert patients.get_by_id(UUID(int=203)) is not None
    assert patients.get_by_id(UUID(int=204)) is None


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
    from app.db.seed import _seed_catalogs, _seed_patients, _seed_working_hours
    from app.repositories.catalog import ChairRepository, ProfessionalRepository, ServiceRepository
    from app.repositories.patients import PatientRepository
    from app.repositories.working_hours import WorkingHoursRepository

    connection.execute(text("DELETE FROM app_user"))
    connection.execute(text("DELETE FROM patient"))
    connection.execute(text("DELETE FROM service"))
    connection.execute(text("DELETE FROM chair"))
    connection.execute(text("DELETE FROM block"))
    connection.execute(text("DELETE FROM working_hours"))
    connection.execute(text("DELETE FROM professional"))
    session = Session(bind=connection)
    _seed_catalogs(session)
    _seed_patients(session)
    _seed_working_hours(session)
    first = {
        "professional": len(ProfessionalRepository(session).list()),
        "chair": len(ChairRepository(session).list()),
        "service": len(ServiceRepository(session).list()),
        "patient": len(PatientRepository(session).list()),
        "working_hours": len(WorkingHoursRepository(session).list()),
    }
    _seed_catalogs(session)
    _seed_patients(session)
    _seed_working_hours(session)
    second = {
        "professional": len(ProfessionalRepository(session).list()),
        "chair": len(ChairRepository(session).list()),
        "service": len(ServiceRepository(session).list()),
        "patient": len(PatientRepository(session).list()),
        "working_hours": len(WorkingHoursRepository(session).list()),
    }
    assert first == {
        "professional": 3,
        "chair": 3,
        "service": 5,
        "patient": 5,
        "working_hours": 25,
    }
    assert second == first


@pytest.mark.parametrize("dni", ["12AB567", "123456"])
def test_patient_dni_check_rejects_invalid_direct_insert(
    connection: Connection,
    dni: str,
) -> None:
    statement = insert(PatientModel).values(
        id=UUID(int=401 if dni == "12AB567" else 402),
        full_name="Paciente CHECK",
        dni=dni,
    )

    try:
        with connection.begin_nested():
            connection.execute(statement)
    except IntegrityError as error:
        raised = error
    else:
        pytest.fail("La inserción inválida no fue rechazada por el CHECK.")

    diagnostic = getattr(raised.orig, "diag", None)
    assert getattr(diagnostic, "constraint_name", None) == "ck_patient_dni_format"
    assert connection.execute(
        text("SELECT count(*) FROM patient WHERE dni = :dni"),
        {"dni": dni},
    ).scalar_one() == 0


def test_invalid_repository_highs_are_rejected_before_persistence(
    connection: Connection,
) -> None:
    from app.repositories.catalog import ProfessionalRepository
    from app.repositories.patients import PatientRepository

    session = Session(bind=connection)
    professionals = ProfessionalRepository(session)
    patients = PatientRepository(session)
    professional_id = UUID(int=403)
    patient_id = UUID(int=404)

    rejected_professional = professionals.create(
        Professional(professional_id, "", True)
    )
    rejected_patient = patients.create(
        Patient(patient_id, "Paciente inválido", "12AB567")
    )

    assert isinstance(rejected_professional, Rejected)
    assert rejected_professional.violations[0].code is ViolationCode.EMPTY_NAME
    assert isinstance(rejected_patient, Rejected)
    assert rejected_patient.violations[0].code is ViolationCode.INVALID_DNI
    assert connection.execute(
        text("SELECT count(*) FROM professional WHERE id = :id"),
        {"id": professional_id},
    ).scalar_one() == 0
    assert connection.execute(
        text("SELECT count(*) FROM patient WHERE id = :id"),
        {"id": patient_id},
    ).scalar_one() == 0


def test_seed_database_is_idempotent_on_test_database(
    test_database_url: URL,
    test_engine: Engine,
) -> None:
    with test_engine.begin() as cleanup_connection:
        cleanup_connection.execute(text("DELETE FROM app_user"))
        cleanup_connection.execute(text("DELETE FROM patient"))
        cleanup_connection.execute(text("DELETE FROM service"))
        cleanup_connection.execute(text("DELETE FROM chair"))
        cleanup_connection.execute(text("DELETE FROM professional"))

    settings = load_settings().model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )

    first = seed_database(settings)
    second = seed_database(settings)

    expected = {
        "professional": 3,
        "chair": 3,
        "service": 5,
        "patient": 5,
        "working_hours": 25,
        "app_user": 3,
    }
    assert first == expected
    assert second == expected

    with test_engine.begin() as cleanup_connection:
        cleanup_connection.execute(text("DELETE FROM app_user"))
        cleanup_connection.execute(text("DELETE FROM patient"))
        cleanup_connection.execute(text("DELETE FROM service"))
        cleanup_connection.execute(text("DELETE FROM chair"))
        cleanup_connection.execute(text("DELETE FROM block"))
        cleanup_connection.execute(text("DELETE FROM working_hours"))
        cleanup_connection.execute(text("DELETE FROM professional"))


def test_concurrent_chair_name_conflict_is_translated(
    connection: Connection,
    test_engine: Engine,
) -> None:
    connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
    session = Session(bind=connection)
    from app.repositories.catalog import ChairRepository

    repository = ChairRepository(session)
    assert all(item.id != UUID(int=500401) for item in repository.list())

    with test_engine.begin() as concurrent_connection:
        concurrent_connection.execute(
            insert(ChairModel).values(
                id=UUID(int=500401),
                name="Sillón 999",
                name_normalized="sillón 999",
            )
        )

    result = repository.create(Chair(UUID(int=500402), "sillón 999", True))

    assert isinstance(result, Rejected)
    assert result.violations[0].code is ViolationCode.DUPLICATE_NAME
    assert result.violations[0].message == (
        'Ya existe un sillón con el nombre "sillón 999".'
    )
    with test_engine.begin() as cleanup_connection:
        cleanup_connection.execute(
            text("DELETE FROM chair WHERE id = :id"),
            {"id": UUID(int=500401)},
        )


def test_patient_unrelated_primary_key_error_is_propagated(
    connection: Connection,
) -> None:
    from app.repositories.patients import PatientRepository

    session = Session(bind=connection)
    repository = PatientRepository(session)
    patient_id = UUID(int=407)
    repository.create(Patient(patient_id, "Paciente PK", "40111222"))

    with pytest.raises(IntegrityError) as raised:
        repository.create(Patient(patient_id, "Paciente PK repetido", "41111222"))

    diagnostic = getattr(raised.value.orig, "diag", None)
    assert getattr(diagnostic, "constraint_name", None) == "pk_patient"


def test_professional_repository_update_and_license_number(
    connection: Connection,
) -> None:
    from app.repositories.catalog import ProfessionalRepository

    session = Session(bind=connection)
    repo = ProfessionalRepository(session)
    prof_id = UUID(int=600101)
    res = repo.create(
        Professional(prof_id, "Dra. Con Matricula", True),
        license_number="MN-12345",
    )
    assert res.__class__ is Ok
    record = repo.get_with_license(prof_id)
    assert record is not None
    assert record.entity == Professional(prof_id, "Dra. Con Matricula", True)
    assert record.license_number == "MN-12345"

    updated = repo.update(
        Professional(prof_id, "Dra. Con Matricula", True),
        license_number="MP-99999",
    )
    assert updated == Ok(Professional(prof_id, "Dra. Con Matricula", True))
    record2 = repo.get_with_license(prof_id)
    assert record2 is not None
    assert record2.license_number == "MP-99999"

    assert repo.update(Professional(UUID(int=999999), "Inexistente", True)) is None

    bad_res = repo.update(Professional(prof_id, "", True))
    assert isinstance(bad_res, Rejected)
    assert bad_res.violations[0].code is ViolationCode.EMPTY_NAME


def test_chair_repository_update_and_exclusion(connection: Connection) -> None:
    from app.repositories.catalog import ChairRepository

    session = Session(bind=connection)
    repo = ChairRepository(session)
    c1 = UUID(int=600201)
    c2 = UUID(int=600202)
    assert repo.create(Chair(c1, "Sillón Alfa", True)).__class__ is Ok
    assert repo.create(Chair(c2, "Sillón Beta", True)).__class__ is Ok

    assert repo.update(Chair(c1, "Sillón Alfa", True)) == Ok(
        Chair(c1, "Sillón Alfa", True)
    )

    assert repo.update(Chair(c1, "Sillón Gamma", True)) == Ok(
        Chair(c1, "Sillón Gamma", True)
    )

    dup = repo.update(Chair(c2, "Sillón Gamma", True))
    assert isinstance(dup, Rejected)
    assert dup.violations[0].code is ViolationCode.DUPLICATE_NAME

    assert repo.update(Chair(UUID(int=999998), "Fantasma", True)) is None


def test_service_repository_update_and_active_filter(connection: Connection) -> None:
    from app.repositories.catalog import ServiceRepository

    session = Session(bind=connection)
    repo = ServiceRepository(session)
    s1 = UUID(int=600301)
    s2 = UUID(int=600302)
    assert repo.create(Service(s1, "Extracción Simple", 30, True)).__class__ is Ok
    assert repo.create(Service(s2, "Limpieza Dental", 45, True)).__class__ is Ok

    # conserving own name
    assert repo.update(Service(s1, "Extracción Simple", 40, True)) == Ok(
        Service(s1, "Extracción Simple", 40, True)
    )

    # duplicate name of s2
    dup = repo.update(Service(s1, "Limpieza Dental", 40, True))
    assert isinstance(dup, Rejected)
    assert dup.violations[0].code is ViolationCode.DUPLICATE_NAME

    # invalid duration
    bad_dur = repo.update(Service(s1, "Extracción Simple", 0, True))
    assert isinstance(bad_dur, Rejected)
    assert bad_dur.violations[0].code is ViolationCode.INVALID_DURATION

    # non-existent
    assert repo.update(Service(UUID(int=999997), "Fantasma", 30, True)) is None

    # test deactivate and active filter
    repo.deactivate(s2)
    all_services = repo.list()
    active_services = repo.list(active=True)
    inactive_services = repo.list(active=False)

    assert any(s.id == s2 for s in all_services)
    assert all(s.id != s2 for s in active_services)
    assert any(s.id == s2 for s in inactive_services)


def test_patient_repository_update_and_search(connection: Connection) -> None:
    from app.repositories.patients import PatientRepository

    session = Session(bind=connection)
    repo = PatientRepository(session)
    p1 = UUID(int=600401)
    p2 = UUID(int=600402)
    assert repo.create(Patient(p1, "Ana Pérez", "30111222", "11223344", "OSDE")).__class__ is Ok
    assert repo.create(Patient(p2, "Carlos Gómez", "30222333", "22334455", "Swiss")).__class__ is Ok

    # update conserving own DNI
    assert repo.update(Patient(p1, "Ana Pérez Modificada", "30111222", "99887766", "Particular")) == Ok(
        Patient(p1, "Ana Pérez Modificada", "30111222", "99887766", "Particular")
    )

    # update with duplicate DNI of p2
    dup = repo.update(Patient(p1, "Ana Pérez Modificada", "30222333", "99887766", "Particular"))
    assert isinstance(dup, Rejected)
    assert dup.violations[0].code is ViolationCode.DUPLICATE_DNI

    # non-existent
    assert repo.update(Patient(UUID(int=999996), "Inexistente", "30999888")) is None

    # search with exact tilde
    found_tilde = repo.list(query="pérez")
    assert any(p.id == p1 for p in found_tilde)

    # search without tilde does NOT match
    not_found_tilde = repo.list(query="perez")
    assert all(p.id != p1 for p in not_found_tilde)

    # search by DNI prefix
    found_dni = repo.list(query="3011")
    assert any(p.id == p1 for p in found_dni)
    assert all(p.id != p2 for p in found_dni)


