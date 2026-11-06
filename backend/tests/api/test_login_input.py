import socket

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest

from app.api.deps import get_current_user
from app.config import Settings
from app.main import create_app


LOGIN = "/api/auth/login"


def closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


@pytest.fixture
def client(api_settings: Settings) -> TestClient:
    # Contra un puerto cerrado: un 400 demuestra que no se consulto al usuario.
    dead_settings = api_settings.model_copy(
        update={
            "database_url": (
                f"postgresql+psycopg://test_user:test_password@127.0.0.1:{closed_port()}/test_db"
            )
        }
    )
    return TestClient(create_app(dead_settings))


def test_missing_password_returns_400(client: TestClient) -> None:
    response = client.post(LOGIN, json={"username": "recepcion"})

    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "password"


def test_too_long_password_returns_400(client: TestClient) -> None:
    response = client.post(LOGIN, json={"username": "recepcion", "password": "x" * 129})

    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "password"


def test_extra_field_returns_400(client: TestClient) -> None:
    response = client.post(
        LOGIN,
        json={"username": "recepcion", "password": "clave-ficticia", "role": "administrador"},
    )

    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "role"


def test_malformed_login_does_not_return_password(client: TestClient) -> None:
    response = client.post(
        LOGIN,
        json={"username": "u" * 151, "password": "contraseña-marcada"},
    )

    assert response.status_code == 400
    assert "contraseña-marcada" not in response.text


def test_response_schemas_have_no_hash(client: TestClient) -> None:
    schema = client.get("/api/openapi.json").json()

    response_schemas = [
        name
        for name in schema["components"]["schemas"]
        if name != "LoginRequest"
    ]
    assert "TokenResponse" in response_schemas
    assert "CurrentUserResponse" in response_schemas
    for name in response_schemas:
        properties = schema["components"]["schemas"][name].get("properties", {})
        assert "passwordHash" not in properties, name
        assert "password_hash" not in properties, name
        assert "password" not in properties, name


def test_malformed_json_on_protected_route_without_token(api_settings: Settings) -> None:
    # Fija el orden de D8: FastAPI parsea el JSON antes de resolver las dependencias,
    # asi que JSON roto en una ruta protegida sin token da 400. No expone datos.
    app = create_app(
        api_settings.model_copy(
            update={
                "database_url": (
                    f"postgresql+psycopg://test_user:test_password@127.0.0.1:{closed_port()}/test_db"
                )
            }
        )
    )
    router = APIRouter()

    class Payload(BaseModel):
        value: int

    @router.post("/api/protected-body", dependencies=[Depends(get_current_user)])
    def protected_body(payload: Payload) -> dict[str, int]:
        return {"value": payload.value}

    app.include_router(router)

    response = TestClient(app).post(
        "/api/protected-body",
        content="{no es json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["errors"][0]["type"] == "json_invalid"
