import traceback
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import Connection, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.model import AuthenticatedUser, StoredUser
from app.db.models import UserModel
from app.domain.model import Role
from app.repositories.users import UserRepository, UserWriteError


pytestmark = pytest.mark.integration

PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-00000000f001")
USER_ID = UUID("00000000-0000-0000-0000-00000000f0a1")
OTHER_ID = UUID("00000000-0000-0000-0000-00000000f0a2")
RECOGNIZABLE_HASH = "hash-ficticio-reconocible"


def reception_user(identifier: UUID = USER_ID) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=identifier,
        username="recepcion",
        display_name="Recepción de Prueba",
        role=Role.RECEPCION,
        professional_id=None,
    )


def full_error_text(error: BaseException) -> str:
    return "".join(traceback.format_exception(error))


def test_get_credentials_returns_hash_for_existing_user(connection: Connection) -> None:
    session = Session(bind=connection)
    repository = UserRepository(session)
    repository.create(reception_user(), RECOGNIZABLE_HASH)

    credentials = repository.get_credentials_by_username("recepcion")

    assert credentials is not None
    assert credentials.password_hash == RECOGNIZABLE_HASH
    assert credentials.user == reception_user()
    assert credentials.active is True


def test_get_credentials_returns_none_for_unknown_user(connection: Connection) -> None:
    repository = UserRepository(Session(bind=connection))

    assert repository.get_credentials_by_username("nadie") is None


def test_get_by_id_returns_user_without_hash(connection: Connection) -> None:
    repository = UserRepository(Session(bind=connection))
    repository.create(reception_user(), RECOGNIZABLE_HASH)

    stored = repository.get_by_id(USER_ID)

    assert stored == StoredUser(user=reception_user(), active=True)
    assert RECOGNIZABLE_HASH not in repr(stored)
    assert not hasattr(stored, "password_hash")
    assert not hasattr(reception_user(), "password_hash")


def test_get_by_id_returns_none_for_unknown_user(connection: Connection) -> None:
    repository = UserRepository(Session(bind=connection))

    assert repository.get_by_id(OTHER_ID) is None


def test_duplicate_username_error_hides_hash(connection: Connection) -> None:
    session = Session(bind=connection)
    repository = UserRepository(session)
    repository.create(reception_user(), "hash-del-primer-usuario")

    with pytest.raises(UserWriteError) as error:
        repository.create(reception_user(OTHER_ID), RECOGNIZABLE_HASH)

    assert error.value.constraint == "ux_app_user_username"
    assert RECOGNIZABLE_HASH not in full_error_text(error.value)

    # El mismo choque sin pasar por el repositorio: lo que tapa el hash es
    # hide_parameters, porque SQLAlchemy incluiria el INSERT con sus parametros.
    with pytest.raises(IntegrityError) as raw_error:
        with session.begin_nested():
            session.add(
                UserModel(
                    id=OTHER_ID,
                    username="recepcion",
                    display_name="Otra Recepción",
                    password_hash=RECOGNIZABLE_HASH,
                    role="recepcion",
                    professional_id=None,
                )
            )
            session.flush()
    assert RECOGNIZABLE_HASH not in full_error_text(raw_error.value)


def test_role_rule_error_hides_hash(connection: Connection) -> None:
    connection.execute(
        text(
            "INSERT INTO professional (id, full_name, active) "
            "VALUES (:id, 'Dra. Ficticia de Prueba', true)"
        ),
        {"id": PROFESSIONAL_ID},
    )
    repository = UserRepository(Session(bind=connection))
    invalid = AuthenticatedUser(
        id=USER_ID,
        username="recepcion",
        display_name="Recepción de Prueba",
        role=Role.RECEPCION,
        professional_id=PROFESSIONAL_ID,
    )

    with pytest.raises(UserWriteError) as error:
        repository.create(invalid, RECOGNIZABLE_HASH)

    assert RECOGNIZABLE_HASH not in full_error_text(error.value)
    assert error.value.constraint == "ck_app_user_professional_by_role"


def test_get_display_names_resolves_in_single_query(connection: Connection) -> None:
    session = Session(bind=connection)
    repository = UserRepository(session)
    admin_user = AuthenticatedUser(
        id=OTHER_ID,
        username="admin",
        display_name="Administración Demo",
        role=Role.ADMINISTRADOR,
        professional_id=None,
    )
    repository.create(reception_user(USER_ID), RECOGNIZABLE_HASH)
    repository.create(admin_user, RECOGNIZABLE_HASH)

    queries: list[str] = []

    def before_cursor_execute(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        queries.append(statement)

    event.listen(connection.engine, "before_cursor_execute", before_cursor_execute)
    try:
        names = repository.get_display_names([
            USER_ID,
            OTHER_ID,
            UUID("00000000-0000-0000-0000-000000000999"),
        ])
    finally:
        event.remove(connection.engine, "before_cursor_execute", before_cursor_execute)

    assert len(queries) == 1
    assert names == {
        USER_ID: "Recepción de Prueba",
        OTHER_ID: "Administración Demo",
    }


def test_get_display_names_empty_list_makes_zero_queries(connection: Connection) -> None:
    session = Session(bind=connection)
    repository = UserRepository(session)

    queries: list[str] = []

    def before_cursor_execute(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        queries.append(statement)

    event.listen(connection.engine, "before_cursor_execute", before_cursor_execute)
    try:
        names = repository.get_display_names([])
    finally:
        event.remove(connection.engine, "before_cursor_execute", before_cursor_execute)

    assert len(queries) == 0
    assert names == {}
