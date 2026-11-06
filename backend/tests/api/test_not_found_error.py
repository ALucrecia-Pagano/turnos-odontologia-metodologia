from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.api.errors import NotFoundError, not_found_error_handler
from app.config import Settings
from app.main import create_app


def test_not_found_error_handler_returns_404_with_unified_body(api_settings: Settings) -> None:
    app = create_app(api_settings)
    router = APIRouter()

    @router.get("/test-not-found")
    def trigger_get_not_found() -> None:
        raise NotFoundError("Profesional no encontrado.")

    @router.put("/test-not-found")
    def trigger_put_not_found() -> None:
        raise NotFoundError("Sillón no encontrado.")

    @router.post("/test-not-found/deactivate")
    def trigger_post_not_found() -> None:
        raise NotFoundError("Prestación no encontrada.")

    app.include_router(router)
    client = TestClient(app)

    # 1. GET
    res_get = client.get("/test-not-found")
    assert res_get.status_code == 404
    assert res_get.json() == {
        "code": "NOT_FOUND",
        "message": "Profesional no encontrado.",
    }

    # 2. PUT
    res_put = client.put("/test-not-found")
    assert res_put.status_code == 404
    assert res_put.json() == {
        "code": "NOT_FOUND",
        "message": "Sillón no encontrado.",
    }

    # 3. POST
    res_post = client.post("/test-not-found/deactivate")
    assert res_post.status_code == 404
    assert res_post.json() == {
        "code": "NOT_FOUND",
        "message": "Prestación no encontrada.",
    }
