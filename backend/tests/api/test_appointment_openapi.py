from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_appointment_create_in_openapi(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    paths = schema["paths"]

    assert "/api/appointments" in paths
    post_op = paths["/api/appointments"]["post"]
    assert "Turnos" in post_op["tags"]

    responses = post_op["responses"]
    assert "201" in responses
    assert "400" in responses
    assert "401" in responses
    assert "403" in responses
    assert "409" in responses
    assert "422" in responses

    schema_201 = responses["201"]["content"]["application/json"]["schema"]
    assert schema_201["$ref"] == "#/components/schemas/AppointmentResponse"
