import re
import socket

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.deps import protected_router
from app.config import Settings
from app.main import create_app
from tests.api.guards import (
    PUBLIC_OPERATIONS,
    protected_routes,
    routes_without_auth,
    routes_without_permission,
    schema_operations,
)


ANY_UUID = "00000000-0000-0000-0000-000000000000"


def closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


@pytest.fixture
def real_app(api_settings: Settings) -> FastAPI:
    return create_app(
        api_settings.model_copy(
            update={
                "database_url": (
                    f"postgresql+psycopg://test_user:test_password@127.0.0.1:{closed_port()}/test_db"
                )
            }
        )
    )


def test_real_non_public_routes_require_token(real_app: FastAPI) -> None:
    assert routes_without_auth(real_app) == set()

    client = TestClient(real_app)
    operations = schema_operations(real_app) - PUBLIC_OPERATIONS
    assert ("GET", "/api/auth/me") in operations
    for method, path in operations:
        response = client.request(method, re.sub(r"\{[^}]+\}", ANY_UUID, path))
        assert response.status_code == 401, f"{method} {path}"


def test_route_without_protection_is_detected(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.get("/api/unprotected")
    def unprotected() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)

    assert routes_without_auth(app) == {("GET", "/api/unprotected")}


def test_real_protected_routes_declare_permission(real_app: FastAPI) -> None:
    assert ("GET", "/api/auth/me") in protected_routes(real_app)
    assert routes_without_permission(real_app) == set()


def test_protected_route_without_permission_is_detected(api_settings: Settings) -> None:
    app = create_app(api_settings)
    # Hereda las dependencias del router protegido, sin tocar el objeto global.
    router = APIRouter(dependencies=protected_router.dependencies)

    @router.get("/api/no-permission")
    def no_permission() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)

    assert routes_without_permission(app) == {("GET", "/api/no-permission")}
    # Fija que la seguridad heredada del router llega al esquema.
    assert routes_without_auth(app) == set()
