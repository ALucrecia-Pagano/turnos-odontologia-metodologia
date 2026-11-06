import socket

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def get_closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


def test_health_returns_503_with_closed_port(api_settings: Settings) -> None:
    closed_port = get_closed_port()
    dead_settings = api_settings.model_copy(
        update={
            "database_url": f"postgresql+psycopg://test_user:test_password@127.0.0.1:{closed_port}/test_db"
        }
    )
    app = create_app(dead_settings)
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}

