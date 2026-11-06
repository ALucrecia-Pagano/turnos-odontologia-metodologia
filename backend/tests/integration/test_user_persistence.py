from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from app.repositories._integrity import constraint_name


pytestmark = pytest.mark.integration

PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-00000000f001")
FICTIONAL_HASH = "hash-ficticio-de-prueba"


def insert_professional(connection: Connection, identifier: UUID = PROFESSIONAL_ID) -> None:
    connection.execute(
        text(
            "INSERT INTO professional (id, full_name, active) "
            "VALUES (:id, 'Dra. Ficticia de Prueba', true)"
        ),
        {"id": identifier},
    )


def insert_user(
    connection: Connection,
    username: str,
    role: str,
    professional_id: UUID | None = None,
) -> UUID:
    identifier = uuid4()
    connection.execute(
        text(
            "INSERT INTO app_user "
            "(id, username, display_name, password_hash, role, professional_id) "
            "VALUES (:id, :username, 'Usuario Ficticio', :hash, :role, :professional_id)"
        ),
        {
            "id": identifier,
            "username": username,
            "hash": FICTIONAL_HASH,
            "role": role,
            "professional_id": professional_id,
        },
    )
    return identifier


def test_duplicate_username_is_rejected(connection: Connection) -> None:
    insert_user(connection, "recepcion", "recepcion")

    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "recepcion", "administrador")

    assert constraint_name(error.value) == "ux_app_user_username"


def test_uppercase_username_is_rejected(connection: Connection) -> None:
    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "Recepcion", "recepcion")

    assert constraint_name(error.value) == "ck_app_user_username_format"


def test_unknown_role_is_rejected(connection: Connection) -> None:
    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "alguien", "superusuario")

    assert constraint_name(error.value) == "ck_app_user_role"


def test_active_defaults_to_true(connection: Connection) -> None:
    identifier = insert_user(connection, "recepcion", "recepcion")

    active = connection.execute(
        text("SELECT active FROM app_user WHERE id = :id"), {"id": identifier}
    ).scalar_one()

    assert active is True


def test_unknown_professional_is_rejected(connection: Connection) -> None:
    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "odontologo", "odontologo", uuid4())

    assert constraint_name(error.value) == "fk_app_user_professional_id_professional"


def test_deleting_professional_with_user_is_rejected(connection: Connection) -> None:
    insert_professional(connection)
    insert_user(connection, "odontologo", "odontologo", PROFESSIONAL_ID)

    with pytest.raises(IntegrityError) as error:
        connection.execute(
            text("DELETE FROM professional WHERE id = :id"), {"id": PROFESSIONAL_ID}
        )

    assert constraint_name(error.value) == "fk_app_user_professional_id_professional"


def test_doctor_with_professional_is_accepted(connection: Connection) -> None:
    insert_professional(connection)

    identifier = insert_user(connection, "odontologo", "odontologo", PROFESSIONAL_ID)

    stored = connection.execute(
        text("SELECT professional_id FROM app_user WHERE id = :id"), {"id": identifier}
    ).scalar_one()
    assert stored == PROFESSIONAL_ID


def test_doctor_without_professional_is_rejected(connection: Connection) -> None:
    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "odontologo", "odontologo", None)

    assert constraint_name(error.value) == "ck_app_user_professional_by_role"


def test_reception_without_professional_is_accepted(connection: Connection) -> None:
    identifier = insert_user(connection, "recepcion", "recepcion", None)

    stored = connection.execute(
        text("SELECT professional_id FROM app_user WHERE id = :id"), {"id": identifier}
    ).scalar_one()
    assert stored is None


def test_reception_with_professional_is_rejected(connection: Connection) -> None:
    insert_professional(connection)

    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "recepcion", "recepcion", PROFESSIONAL_ID)

    assert constraint_name(error.value) == "ck_app_user_professional_by_role"


def test_admin_with_professional_is_rejected(connection: Connection) -> None:
    insert_professional(connection)

    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "administrador", "administrador", PROFESSIONAL_ID)

    assert constraint_name(error.value) == "ck_app_user_professional_by_role"


def test_changing_role_keeping_professional_is_rejected(connection: Connection) -> None:
    insert_professional(connection)
    identifier = insert_user(connection, "odontologo", "odontologo", PROFESSIONAL_ID)

    with pytest.raises(IntegrityError) as error:
        connection.execute(
            text("UPDATE app_user SET role = 'recepcion' WHERE id = :id"),
            {"id": identifier},
        )

    assert constraint_name(error.value) == "ck_app_user_professional_by_role"


def test_two_users_for_same_professional_are_rejected(connection: Connection) -> None:
    insert_professional(connection)
    insert_user(connection, "odontologo", "odontologo", PROFESSIONAL_ID)

    with pytest.raises(IntegrityError) as error:
        insert_user(connection, "odontologo2", "odontologo", PROFESSIONAL_ID)

    assert constraint_name(error.value) == "ux_app_user_professional_id"


def test_several_users_without_professional_are_accepted(connection: Connection) -> None:
    insert_user(connection, "recepcion", "recepcion", None)
    insert_user(connection, "administrador", "administrador", None)

    count = connection.execute(
        text("SELECT count(*) FROM app_user WHERE professional_id IS NULL")
    ).scalar_one()
    assert count == 2
