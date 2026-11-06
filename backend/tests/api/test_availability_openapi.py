from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_availability_routes_in_openapi(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    paths = schema["paths"]

    # 1. GET /api/professionals/{id}/working-hours
    assert "/api/professionals/{id}/working-hours" in paths
    wh_get = paths["/api/professionals/{id}/working-hours"]["get"]
    assert "Horarios" in wh_get["tags"]
    assert "200" in wh_get["responses"]
    assert "401" in wh_get["responses"]
    assert "403" in wh_get["responses"]
    assert "404" in wh_get["responses"]

    # 2. PUT /api/professionals/{id}/working-hours
    wh_put = paths["/api/professionals/{id}/working-hours"]["put"]
    assert "Horarios" in wh_put["tags"]
    assert "200" in wh_put["responses"]
    assert "400" in wh_put["responses"]
    assert "401" in wh_put["responses"]
    assert "403" in wh_put["responses"]
    assert "404" in wh_put["responses"]
    assert "422" in wh_put["responses"]

    # 3. GET /api/professionals/{id}/blocks
    assert "/api/professionals/{id}/blocks" in paths
    blocks_get = paths["/api/professionals/{id}/blocks"]["get"]
    assert "Bloqueos" in blocks_get["tags"]
    assert "200" in blocks_get["responses"]
    assert "400" in blocks_get["responses"]
    assert "401" in blocks_get["responses"]
    assert "403" in blocks_get["responses"]
    assert "404" in blocks_get["responses"]

    # 4. POST /api/professionals/{id}/blocks
    blocks_post = paths["/api/professionals/{id}/blocks"]["post"]
    assert "Bloqueos" in blocks_post["tags"]
    assert "201" in blocks_post["responses"]
    assert "400" in blocks_post["responses"]
    assert "401" in blocks_post["responses"]
    assert "403" in blocks_post["responses"]
    assert "404" in blocks_post["responses"]
    assert "422" in blocks_post["responses"]

    # 5. DELETE /api/blocks/{block_id}
    assert "/api/blocks/{block_id}" in paths
    blocks_delete = paths["/api/blocks/{block_id}"]["delete"]
    assert "Bloqueos" in blocks_delete["tags"]
    assert "200" in blocks_delete["responses"]
    assert "401" in blocks_delete["responses"]
    assert "403" in blocks_delete["responses"]
    assert "404" in blocks_delete["responses"]
