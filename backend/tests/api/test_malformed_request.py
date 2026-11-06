from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.config import Settings
from app.main import create_app


class SampleBody(BaseModel):
    start_at: str = Field(alias="startAt")


class CountBody(BaseModel):
    count: int


def test_invalid_json_returns_400(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/sample")
    def sample_endpoint(body: SampleBody) -> dict[str, str]:
        return {"ok": body.start_at}

    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/sample",
        content="esto no es json{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "errors" in data
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["type"] == "json_invalid"
    assert data["errors"][0]["message"] == "El cuerpo no es JSON válido."


def test_missing_field_returns_400(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/sample")
    def sample_endpoint(body: SampleBody) -> dict[str, str]:
        return {"ok": body.start_at}

    app.include_router(router)
    client = TestClient(app)

    response = client.post("/sample", json={})
    assert response.status_code == 400
    data = response.json()
    assert "errors" in data
    assert data["errors"][0]["field"] == "startAt"
    assert data["errors"][0]["type"] == "missing"
    assert data["errors"][0]["message"] == "Falta este dato."


def test_sent_value_is_not_returned(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.post("/count")
    def count_endpoint(body: CountBody) -> dict[str, int]:
        return {"ok": body.count}

    app.include_router(router)
    client = TestClient(app)

    response = client.post("/count", json={"count": "valor-marcado-c18"})
    assert response.status_code == 400
    assert "valor-marcado-c18" not in response.text


def test_invalid_query_param_returns_400(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.get("/query-test")
    def query_endpoint(
        professional_id: UUID = Query(alias="professionalId"),
    ) -> dict[str, str]:
        return {"ok": str(professional_id)}

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/query-test?professionalId=no-es-uuid")
    assert response.status_code == 400
    data = response.json()
    assert "errors" in data
    assert data["errors"][0]["field"] == "professionalId"

