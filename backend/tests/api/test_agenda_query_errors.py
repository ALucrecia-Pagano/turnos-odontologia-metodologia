from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.testclient import TestClient

from app.api.schemas import AgendaQuery
from app.config import Settings
from app.main import create_app


def day(offset: int = 0) -> str:
    return (date.today() + timedelta(days=30 + offset)).isoformat()


def build_client(api_settings: Settings) -> TestClient:
    app = create_app(api_settings)
    router = APIRouter()

    @router.get("/sample-agenda")
    def sample_agenda(params: Annotated[AgendaQuery, Query()]) -> dict[str, str]:
        return {"from": params.from_date.isoformat(), "to": params.to_date.isoformat()}

    app.include_router(router)
    return TestClient(app)


def test_agenda_query_errors_return_400_with_spanish_messages(api_settings: Settings) -> None:
    client = build_client(api_settings)

    ok = client.get("/sample-agenda", params={"from": day(), "to": day()})
    assert ok.status_code == 200
    assert ok.json() == {"from": day(), "to": day()}

    cases = [
        ({"from": "09-11-2026", "to": day()}, "from", "invalid_date_format",
         "La fecha debe tener formato AAAA-MM-DD."),
        ({"from": day(1), "to": day()}, None, "invalid_range_order",
         "La fecha final no puede ser anterior a la inicial."),
        ({"from": day(), "to": day(31)}, None, "invalid_range_length",
         "El rango no puede superar los 31 días."),
        ({"to": day()}, "from", "missing", "Falta este dato."),
        ({"from": day(), "to": day(), "status": "cancelado"}, "status",
         "extra_forbidden", "Dato inválido."),
    ]
    for params, field, err_type, message in cases:
        response = client.get("/sample-agenda", params=params)
        assert response.status_code == 400, params
        assert response.json() == {
            "errors": [{"field": field, "type": err_type, "message": message}]
        }, params
