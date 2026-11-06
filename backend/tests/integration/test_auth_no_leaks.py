import logging

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text

from tests.integration.auth_support import LOGIN, ME, PASSWORD, RECEPTION_ID


pytestmark = pytest.mark.integration


def stored_hash(engine: Engine) -> str:
    with engine.connect() as connection:
        value: str = connection.execute(
            text("SELECT password_hash FROM app_user WHERE id = :id"), {"id": RECEPTION_ID}
        ).scalar_one()
    return value


def keys_of(value: object) -> set[str]:
    if isinstance(value, dict):
        nested = {key for item in value.values() for key in keys_of(item)}
        return {str(key) for key in value} | nested
    if isinstance(value, list):
        return {key for item in value for key in keys_of(item)}
    return set()


def assert_no_password_keys(body: object) -> None:
    assert not [key for key in keys_of(body) if key.lower().startswith("password")]


def test_login_response_has_no_secrets(auth_client: TestClient, test_engine: Engine) -> None:
    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    assert response.status_code == 200
    assert PASSWORD not in response.text
    assert stored_hash(test_engine) not in response.text
    assert_no_password_keys(response.json())


def test_me_response_has_no_secrets(auth_client: TestClient, test_engine: Engine) -> None:
    token = auth_client.post(
        LOGIN, json={"username": "recepcion", "password": PASSWORD}
    ).json()["accessToken"]

    response = auth_client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert stored_hash(test_engine) not in response.text
    assert_no_password_keys(response.json())


def test_successful_login_logs_no_secrets(
    auth_client: TestClient, test_engine: Engine, caplog: pytest.LogCaptureFixture
) -> None:
    password_hash = stored_hash(test_engine)
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="sqlalchemy.engine")

    response = auth_client.post(LOGIN, json={"username": "recepcion", "password": PASSWORD})

    assert response.status_code == 200
    assert PASSWORD not in caplog.text
    assert password_hash not in caplog.text
    assert response.json()["accessToken"] not in caplog.text


def test_failed_login_logs_no_secrets(
    auth_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="sqlalchemy.engine")

    response = auth_client.post(
        LOGIN, json={"username": "recepcion", "password": "contraseña-marcada-incorrecta"}
    )

    assert response.status_code == 401
    assert "contraseña-marcada-incorrecta" not in caplog.text
    assert PASSWORD not in caplog.text
