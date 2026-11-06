from fastapi.testclient import TestClient
import pytest
from sqlalchemy.engine import URL

from app.config import Settings
from app.main import create_app


@pytest.mark.integration
def test_health_returns_200_with_database(
    integration_settings: Settings,
    test_database_url: URL,
) -> None:
    test_settings = integration_settings.model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )
    app = create_app(test_settings)
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}

