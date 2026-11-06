from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_preflight_allowed_from_cors_origin(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_simple_response_allowed_from_cors_origin(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_preflight_rejected_from_other_origin(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://otro-origen.test",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert "access-control-allow-origin" not in response.headers

