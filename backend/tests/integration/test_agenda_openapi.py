from fastapi.testclient import TestClient
import pytest

pytestmark = pytest.mark.integration


def test_agenda_openapi_documents_parameters_responses_and_models(
    auth_client: TestClient,
) -> None:
    schema = auth_client.get("/api/openapi.json").json()
    operation = schema["paths"]["/api/agenda"]["get"]

    assert operation["tags"] == ["Agenda"]
    for code in ("200", "400", "401", "403"):
        assert code in operation["responses"], code
    assert "404" not in operation["responses"]
    assert "409" not in operation["responses"]
    assert "422" not in operation["responses"]

    parameters = {p["name"]: p for p in operation["parameters"]}
    assert set(parameters) == {"from", "to", "professionalId", "chairId"}
    assert parameters["from"]["required"] is True
    assert parameters["to"]["required"] is True
    assert parameters["professionalId"]["required"] is False
    assert parameters["chairId"]["required"] is False
    assert "inclusiva" in parameters["to"]["description"]
    assert "AAAA-MM-DD" in parameters["from"]["description"]

    ok = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert ok["$ref"] == "#/components/schemas/AgendaResponse"
    envelope = schema["components"]["schemas"]["AgendaResponse"]
    assert set(envelope["properties"]) == {
        "from",
        "to",
        "timezone",
        "appointments",
        "workingHours",
        "blocks",
    }
    assert (
        envelope["properties"]["appointments"]["items"]["$ref"]
        == "#/components/schemas/AgendaAppointmentResponse"
    )


def test_appointment_detail_openapi_documents_responses_and_model(
    auth_client: TestClient,
) -> None:
    schema = auth_client.get("/api/openapi.json").json()
    operation = schema["paths"]["/api/appointments/{id}"]["get"]

    assert operation["tags"] == ["Turnos"]
    for code in ("200", "400", "401", "403", "404"):
        assert code in operation["responses"], code
    assert "409" not in operation["responses"]
    assert "422" not in operation["responses"]
    ok = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert ok["$ref"] == "#/components/schemas/AgendaAppointmentResponse"
    not_found = operation["responses"]["404"]["content"]["application/json"]["example"]
    assert not_found == {"code": "NOT_FOUND", "message": "Turno no encontrado."}
