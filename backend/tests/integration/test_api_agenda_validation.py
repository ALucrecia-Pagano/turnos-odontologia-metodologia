from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from tests.integration.agenda_api_support import agenda_data, future_monday, token_for

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("agenda_data")]

__all__ = ["agenda_data"]


def get_errors(client: TestClient, params: dict[str, str]) -> list[dict[str, object]]:
    headers = token_for(client, "recepcion")
    res = client.get("/api/agenda", params=params, headers=headers)
    assert res.status_code == 400, res.text
    body = res.json()
    assert list(body) == ["errors"]
    errors: list[dict[str, object]] = body["errors"]
    return errors


def test_missing_from_returns_400(auth_client: TestClient) -> None:
    monday = future_monday()
    assert get_errors(auth_client, {"to": monday.isoformat()}) == [
        {"field": "from", "type": "missing", "message": "Falta este dato."}
    ]


def test_missing_to_returns_400(auth_client: TestClient) -> None:
    monday = future_monday()
    assert get_errors(auth_client, {"from": monday.isoformat()}) == [
        {"field": "to", "type": "missing", "message": "Falta este dato."}
    ]


def test_invalid_date_format_returns_400(auth_client: TestClient) -> None:
    monday = future_monday()
    wrong = monday.strftime("%d-%m-%Y")
    assert get_errors(auth_client, {"from": wrong, "to": monday.isoformat()}) == [
        {
            "field": "from",
            "type": "invalid_date_format",
            "message": "La fecha debe tener formato AAAA-MM-DD.",
        }
    ]


def test_to_before_from_returns_400(auth_client: TestClient) -> None:
    monday = future_monday()
    tuesday = monday + timedelta(days=1)
    assert get_errors(auth_client, {"from": tuesday.isoformat(), "to": monday.isoformat()}) == [
        {
            "field": None,
            "type": "invalid_range_order",
            "message": "La fecha final no puede ser anterior a la inicial.",
        }
    ]


def test_range_longer_than_31_days_returns_400(auth_client: TestClient) -> None:
    monday = future_monday()
    too_far = monday + timedelta(days=31)
    assert get_errors(auth_client, {"from": monday.isoformat(), "to": too_far.isoformat()}) == [
        {
            "field": None,
            "type": "invalid_range_length",
            "message": "El rango no puede superar los 31 días.",
        }
    ]


def test_malformed_professional_id_returns_400(auth_client: TestClient) -> None:
    monday = future_monday().isoformat()
    assert get_errors(
        auth_client, {"from": monday, "to": monday, "professionalId": "no-es-un-uuid"}
    ) == [{"field": "professionalId", "type": "uuid_parsing", "message": "Dato inválido."}]


def test_malformed_chair_id_returns_400(auth_client: TestClient) -> None:
    monday = future_monday().isoformat()
    assert get_errors(auth_client, {"from": monday, "to": monday, "chairId": "no-es-un-uuid"}) == [
        {"field": "chairId", "type": "uuid_parsing", "message": "Dato inválido."}
    ]


def test_unknown_query_parameter_returns_400(auth_client: TestClient) -> None:
    monday = future_monday().isoformat()
    assert get_errors(auth_client, {"from": monday, "to": monday, "status": "cancelado"}) == [
        {"field": "status", "type": "extra_forbidden", "message": "Dato inválido."}
    ]


def test_agenda_without_token_returns_401(auth_client: TestClient) -> None:
    monday = future_monday().isoformat()
    res = auth_client.get("/api/agenda", params={"from": monday, "to": monday})
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_TOKEN"
