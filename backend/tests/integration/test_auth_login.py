from uuid import UUID

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import Engine, text

from tests.integration.auth_support import (
    INVALID_CREDENTIALS_BODY,
    LOGIN,
    PASSWORD,
    RECEPTION_ID,
)


pytestmark = pytest.mark.integration


def set_inactive(engine: Engine, identifier: UUID) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE app_user SET active = false WHERE id = :id"), {"id": identifier}
        )


@pytest.mark.parametrize("username", ["administrador", "recepcion", "odontologo"])
def test_login_success(username: str, auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": username, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"accessToken", "tokenType"}
    assert body["tokenType"] == "bearer"


def test_login_response_has_no_store(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    assert response.headers["Cache-Control"] == "no-store"


def test_login_normalizes_username(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": "  Recepcion ", "password": PASSWORD})

    assert response.status_code == 200


def test_login_token_matches_user(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    payload = jwt.decode(response.json()["accessToken"], options={"verify_signature": False})
    assert payload["sub"] == str(RECEPTION_ID)
    assert payload["role"] == "recepcion"


def test_wrong_password_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": "otra-clave"})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_unknown_user_is_rejected(auth_client: TestClient) -> None:
    response = auth_client.post(LOGIN, json={"username": "nadie", "password": PASSWORD})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY


def test_inactive_user_with_correct_password_is_rejected(
    auth_client: TestClient, test_engine: Engine
) -> None:
    set_inactive(test_engine, RECEPTION_ID)

    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY


def test_inactive_user_with_wrong_password_is_rejected(
    auth_client: TestClient, test_engine: Engine
) -> None:
    set_inactive(test_engine, RECEPTION_ID)

    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": "otra-clave"})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY


def test_invalid_credentials_are_byte_identical(
    auth_client: TestClient, test_engine: Engine
) -> None:
    wrong_password = auth_client.post(
        LOGIN, json={"username": "recepcion", "password": "otra-clave"}
    )
    unknown_user = auth_client.post(LOGIN, json={"username": "nadie", "password": PASSWORD})
    set_inactive(test_engine, RECEPTION_ID)
    inactive_correct = auth_client.post(
        LOGIN, json={"username": "recepcion", "password": PASSWORD}
    )
    inactive_wrong = auth_client.post(
        LOGIN, json={"username": "recepcion", "password": "otra-clave"}
    )
    responses = (wrong_password, unknown_user, inactive_correct, inactive_wrong)

    assert {response.status_code for response in responses} == {401}
    assert len({response.content for response in responses}) == 1
    assert len({response.headers["WWW-Authenticate"] for response in responses}) == 1
    assert len({response.headers["Content-Type"] for response in responses}) == 1


def test_corrupt_stored_hash_is_rejected(
    auth_client: TestClient, test_engine: Engine
) -> None:
    with test_engine.begin() as connection:
        connection.execute(
            text("UPDATE app_user SET password_hash = 'no-es-un-hash' WHERE id = :id"),
            {"id": RECEPTION_ID},
        )

    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_BODY
