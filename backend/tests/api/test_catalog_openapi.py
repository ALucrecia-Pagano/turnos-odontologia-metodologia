from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_catalog_and_patient_routes_in_openapi(api_settings: Settings) -> None:
    app = create_app(api_settings)
    client = TestClient(app)

    schema = client.get("/api/openapi.json").json()
    paths = schema["paths"]

    # Verify routes exist
    assert "/api/professionals" in paths
    assert "/api/professionals/{id}" in paths
    assert "/api/professionals/{id}/deactivate" in paths
    assert "/api/professionals/{id}/reactivate" in paths

    assert "/api/chairs" in paths
    assert "/api/chairs/{id}" in paths
    assert "/api/chairs/{id}/deactivate" in paths
    assert "/api/chairs/{id}/reactivate" in paths

    assert "/api/services" in paths
    assert "/api/services/{id}" in paths
    assert "/api/services/{id}/deactivate" in paths
    assert "/api/services/{id}/reactivate" in paths

    assert "/api/patients" in paths
    assert "/api/patients/{id}" in paths
    # Patients have NO deactivate and NO delete
    assert "/api/patients/{id}/deactivate" not in paths

    # Verify every route with {id} documents 404
    for path, operations in paths.items():
        if "{id}" in path:
            for method, op in operations.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    assert "404" in op["responses"], f"{method.upper()} {path} missing 404 documentation"

    # Verify every protected route documents 401 and 403
    for path, operations in paths.items():
        if path.startswith(("/api/professionals", "/api/chairs", "/api/services", "/api/patients")):
            for method, op in operations.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    assert "401" in op["responses"], f"{method.upper()} {path} missing 401 documentation"
                    assert "403" in op["responses"], f"{method.upper()} {path} missing 403 documentation"
