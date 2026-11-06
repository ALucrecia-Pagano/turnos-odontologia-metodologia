"""Usuarios de prueba para los tests de integración de autenticación.

Se insertan con el hash barato: `verify` usa los parámetros del hash, así que los
tests son rápidos sin que producción tenga ningún parámetro que baje el costo.
"""

from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

from tests.auth.hashes import cheap_hash


PASSWORD = "clave-ficticia-de-prueba"
PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_PROFESSIONAL_ID = UUID("00000000-0000-0000-0000-000000000002")
ADMIN_ID = UUID("00000000-0000-0000-0000-0000000000e1")
RECEPTION_ID = UUID("00000000-0000-0000-0000-0000000000e2")
DOCTOR_ID = UUID("00000000-0000-0000-0000-0000000000e3")
LOGIN = "/api/auth/login"
ME = "/api/auth/me"
INVALID_TOKEN_BODY = {
    "code": "INVALID_TOKEN",
    "message": "La sesión venció o no es válida. Inicie sesión de nuevo.",
}
INVALID_CREDENTIALS_BODY = {
    "code": "INVALID_CREDENTIALS",
    "message": "Usuario o contraseña incorrectos.",
}


def insert_professional(connection: Connection, identifier: UUID, name: str) -> None:
    connection.execute(
        text(
            "INSERT INTO professional (id, full_name, active) "
            "VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"
        ),
        {"id": identifier, "name": name},
    )


def insert_user(
    connection: Connection,
    identifier: UUID,
    username: str,
    role: str,
    professional_id: UUID | None,
    password_hash: str,
) -> None:
    connection.execute(
        text(
            "INSERT INTO app_user "
            "(id, username, display_name, password_hash, role, professional_id) "
            "VALUES (:id, :username, :display_name, :hash, :role, :professional_id)"
        ),
        {
            "id": identifier,
            "username": username,
            "display_name": f"Usuario Ficticio {username}",
            "hash": password_hash,
            "role": role,
            "professional_id": professional_id,
        },
    )


def create_auth_users(engine: Engine) -> None:
    remove_auth_users(engine)
    password_hash = cheap_hash(PASSWORD)
    with engine.begin() as connection:
        insert_professional(connection, PROFESSIONAL_ID, "Dra. Ficticia Uno")
        insert_professional(connection, OTHER_PROFESSIONAL_ID, "Dr. Ficticio Dos")
        insert_user(connection, ADMIN_ID, "administrador", "administrador", None, password_hash)
        insert_user(connection, RECEPTION_ID, "recepcion", "recepcion", None, password_hash)
        insert_user(connection, DOCTOR_ID, "odontologo", "odontologo", PROFESSIONAL_ID, password_hash)


def remove_auth_users(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM app_user"))
        connection.execute(
            text("DELETE FROM professional WHERE id IN (:first, :second)"),
            {"first": PROFESSIONAL_ID, "second": OTHER_PROFESSIONAL_ID},
        )
