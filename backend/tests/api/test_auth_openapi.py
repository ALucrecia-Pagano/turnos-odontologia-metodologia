from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.api.deps import protected_router, require_permission
from app.api.openapi import permission_responses
from app.auth.permissions import Action, Resource
from app.config import Settings
from app.main import create_app


AUTH_ERROR_REF = "#/components/schemas/AuthErrorResponse"
VIOLATION_REF = "#/components/schemas/ViolationResponseSchema"


def test_bearer_scheme_is_declared(api_settings: Settings) -> None:
    client = TestClient(create_app(api_settings))

    schemes = client.get("/api/openapi.json").json()["components"]["securitySchemes"]

    assert schemes["bearerAuth"]["type"] == "http"
    assert schemes["bearerAuth"]["scheme"] == "bearer"
    assert schemes["bearerAuth"]["bearerFormat"] == "JWT"


def test_me_has_security_and_401(api_settings: Settings) -> None:
    client = TestClient(create_app(api_settings))

    schema = client.get("/api/openapi.json").json()
    operation = schema["paths"]["/api/auth/me"]["get"]

    assert operation["security"] == [{"bearerAuth": []}]
    assert operation["responses"]["401"]["content"]["application/json"]["schema"]["$ref"] == AUTH_ERROR_REF
    assert "AuthErrorResponse" in schema["components"]["schemas"]


def test_login_has_no_security_and_documents_responses(api_settings: Settings) -> None:
    client = TestClient(create_app(api_settings))

    operation = client.get("/api/openapi.json").json()["paths"]["/api/auth/login"]["post"]

    assert "security" not in operation
    assert {"200", "400", "401"} <= set(operation["responses"])
    assert operation["responses"]["401"]["content"]["application/json"]["schema"]["$ref"] == AUTH_ERROR_REF


def test_health_has_no_security(api_settings: Settings) -> None:
    client = TestClient(create_app(api_settings))

    operation = client.get("/api/openapi.json").json()["paths"]["/api/health"]["get"]

    assert "security" not in operation


def test_permission_route_documents_403(api_settings: Settings) -> None:
    app = create_app(api_settings)
    # Hereda las dependencias del router protegido, sin tocar el objeto global.
    router = APIRouter(dependencies=protected_router.dependencies)

    @router.post(
        "/api/permission-route",
        responses=permission_responses(),
        dependencies=[Depends(require_permission(Resource.APPOINTMENT, Action.CREATE))],
    )
    def permission_route() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)

    operation = TestClient(app).get("/api/openapi.json").json()["paths"][
        "/api/permission-route"
    ]["post"]

    assert operation["responses"]["403"]["content"]["application/json"]["schema"]["$ref"] == VIOLATION_REF
    assert operation["responses"]["401"]["content"]["application/json"]["schema"]["$ref"] == AUTH_ERROR_REF


def test_swagger_persists_authorization(api_settings: Settings) -> None:
    response = TestClient(create_app(api_settings)).get("/api/docs")

    assert response.status_code == 200
    assert "persistAuthorization" in response.text
