from uuid import UUID

from app.domain.model import Chair, Patient, Professional, Service


def test_demo_data_fictional_entities_are_available() -> None:
    from app import demo_data

    assert len(demo_data.PROFESSIONALS) == 3
    assert len(demo_data.CHAIRS) == 3
    assert len(demo_data.SERVICES) == 5
    assert len(demo_data.PATIENTS) == 5
    assert demo_data.PROFESSIONALS[0] == Professional(
        UUID("00000000-0000-0000-0000-000000000001"), "Dra. Laura Quiroga", True
    )
    assert demo_data.PATIENTS[0] == Patient(
        UUID("00000000-0000-0000-0000-0000000000c1"), "Ana Pérez", "30111222"
    )


def test_demo_professional_accepted_by_public_create() -> None:
    from app import demo_data
    from app.domain.catalog.create import create_professional
    from app.domain.catalog.result import Ok

    before = demo_data.PROFESSIONALS
    candidate = before[0]
    assert create_professional(candidate) == Ok(candidate)
    assert demo_data.PROFESSIONALS == before


def test_demo_chair_accepted_by_public_create() -> None:
    from app import demo_data
    from app.domain.catalog.create import create_chair
    from app.domain.catalog.result import Ok

    before = demo_data.CHAIRS
    candidate = before[0]
    assert create_chair(candidate, ()) == Ok(candidate)
    assert demo_data.CHAIRS == before


def test_demo_service_accepted_by_public_create() -> None:
    from app import demo_data
    from app.domain.catalog.create import create_service
    from app.domain.catalog.result import Ok

    before = demo_data.SERVICES
    candidate = before[0]
    assert create_service(candidate, ()) == Ok(candidate)
    assert demo_data.SERVICES == before


def test_demo_patient_accepted_by_public_create() -> None:
    from app import demo_data
    from app.domain.catalog.create import create_patient
    from app.domain.catalog.result import Ok

    before = demo_data.PATIENTS
    candidate = before[0]
    assert create_patient(candidate, ()) == Ok(candidate)
    assert demo_data.PATIENTS == before


def test_demo_users_are_fictional_one_per_role() -> None:
    from app import demo_data
    from app.domain.model import Role

    assert [(user.username, user.role, user.professional_id) for user in demo_data.USERS] == [
        ("administrador", Role.ADMINISTRADOR, None),
        ("recepcion", Role.RECEPCION, None),
        ("odontologo", Role.ODONTOLOGO, demo_data.PROFESSIONALS[0].id),
    ]
    assert [user.id for user in demo_data.USERS] == [
        UUID("00000000-0000-0000-0000-0000000000e1"),
        UUID("00000000-0000-0000-0000-0000000000e2"),
        UUID("00000000-0000-0000-0000-0000000000e3"),
    ]
    assert [user.display_name for user in demo_data.USERS] == [
        "Administración Demo",
        "Recepción Demo",
        "Dra. Laura Quiroga",
    ]
    assert not hasattr(demo_data.USERS[0], "password")
    assert not hasattr(demo_data.USERS[0], "password_hash")
