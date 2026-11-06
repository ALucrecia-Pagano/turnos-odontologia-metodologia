from typing import Any

from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.openapi import violation_responses
from app.config import Settings
from app.domain.violations import ViolationCode
from app.main import create_app


class DummyInput(BaseModel):
    name: str


def test_swagger_served_at_api_docs(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_automatic_422_is_removed(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/dummy")
    def dummy_route(payload: DummyInput) -> dict[str, str]:
        return {"name": payload.name}

    app.include_router(router)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    op = schema["paths"]["/dummy"]["post"]
    assert "422" not in op["responses"]
    components = schema.get("components", {}).get("schemas", {})
    assert "HTTPValidationError" not in components
    assert "ValidationError" not in components


def test_400_documented_on_route_with_input(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/dummy")
    def dummy_route(payload: DummyInput) -> dict[str, str]:
        return {"name": payload.name}

    app.include_router(router)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    op = schema["paths"]["/dummy"]["post"]
    assert "400" in op["responses"]


def test_409_documented_on_rejecting_route(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/dummy", responses=violation_responses(409))
    def dummy_route(payload: DummyInput) -> dict[str, str]:
        return {"name": payload.name}

    app.include_router(router)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    op = schema["paths"]["/dummy"]["post"]
    assert "409" in op["responses"]


def test_422_documented_on_rejecting_route(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/dummy", responses=violation_responses(422))
    def dummy_route(payload: DummyInput) -> dict[str, str]:
        return {"name": payload.name}

    app.include_router(router)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    op = schema["paths"]["/dummy"]["post"]
    assert "422" in op["responses"]


def test_schema_lists_all_violation_codes(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/dummy", responses=violation_responses(409))
    def dummy_route(payload: DummyInput) -> dict[str, str]:
        return {"name": payload.name}

    app.include_router(router)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    components: dict[str, Any] = schema["components"]["schemas"]
    violation_code_enum = components.get("ViolationCode", {}).get("enum")
    if violation_code_enum is None:
        violation_code_enum = components["ViolationItemSchema"]["properties"]["code"]["enum"]

    assert set(violation_code_enum) == {code.value for code in ViolationCode}


def test_health_documents_200_and_503(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    health_op = schema["paths"]["/api/health"]["get"]
    assert "200" in health_op["responses"]
    assert "503" in health_op["responses"]

