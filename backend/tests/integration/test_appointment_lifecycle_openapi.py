from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration


def test_appointment_lifecycle_openapi_documentation(auth_client: TestClient) -> None:
    schema = auth_client.get("/api/openapi.json").json()
    paths = schema["paths"]

    cancel_path = paths["/api/appointments/{id}/cancel"]["post"]
    reschedule_path = paths["/api/appointments/{id}/reschedule"]["post"]
    status_path = paths["/api/appointments/{id}/status"]["post"]
    history_path = paths["/api/appointments/{id}/history"]["get"]

    for op in (cancel_path, reschedule_path, status_path, history_path):
        assert "Turnos" in op["tags"]
        responses = op["responses"]
        for code in ("200", "400", "401", "403", "404"):
            assert code in responses, f"{code} faltante en {op}"

    # 422 en cancel, reschedule, status
    assert "422" in cancel_path["responses"]
    assert "422" in reschedule_path["responses"]
    assert "422" in status_path["responses"]

    # 409 solo en reschedule
    assert "409" in reschedule_path["responses"]
    assert "409" not in cancel_path["responses"]
    assert "409" not in status_path["responses"]

    # history no documenta 409 ni 422 de dominio
    assert "409" not in history_path["responses"]
    assert "422" not in history_path["responses"]

    # Modelos de respuesta
    cancel_200 = cancel_path["responses"]["200"]["content"]["application/json"]["schema"]
    assert cancel_200["$ref"] == "#/components/schemas/AppointmentResponse"

    resched_200 = reschedule_path["responses"]["200"]["content"]["application/json"]["schema"]
    assert resched_200["$ref"] == "#/components/schemas/AppointmentResponse"

    status_200 = status_path["responses"]["200"]["content"]["application/json"]["schema"]
    assert status_200["$ref"] == "#/components/schemas/AppointmentResponse"

    history_200 = history_path["responses"]["200"]["content"]["application/json"]["schema"]
    assert history_200["items"]["$ref"] == "#/components/schemas/HistoryEntryResponse"
