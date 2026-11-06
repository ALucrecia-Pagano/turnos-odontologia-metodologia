from collections.abc import Iterator
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text

from tests.integration.auth_support import LOGIN, PASSWORD

pytestmark = pytest.mark.integration

FAKE_ID = "00000000-0000-0000-0000-ffffffffffff"


@pytest.fixture(autouse=True)
def clean_services_table(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM service"))
    yield



def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def test_create_service_responds_201(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(
        "/api/services",
        json={"name": "Endodoncia Multirradicular", "defaultDurationMin": 60},
        headers=admin_h,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Endodoncia Multirradicular"
    assert data["defaultDurationMin"] == 60
    assert data["active"] is True


def test_update_service_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/services",
        json={"name": "Prótesis Parcial", "defaultDurationMin": 45},
        headers=admin_h,
    ).json()
    srv_id = created["id"]

    res = auth_client.put(
        f"/api/services/{srv_id}",
        json={"name": "Prótesis Parcial Removible", "defaultDurationMin": 50},
        headers=admin_h,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Prótesis Parcial Removible"
    assert res.json()["defaultDurationMin"] == 50


def test_update_service_conserving_own_name_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/services",
        json={"name": "Blanqueamiento Láser", "defaultDurationMin": 40},
        headers=admin_h,
    ).json()
    srv_id = created["id"]

    res = auth_client.put(
        f"/api/services/{srv_id}",
        json={"name": "Blanqueamiento Láser", "defaultDurationMin": 45},
        headers=admin_h,
    )
    assert res.status_code == 200
    assert res.json()["defaultDurationMin"] == 45


def test_update_service_with_name_of_another_responds_409(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s1 = auth_client.post(
        "/api/services",
        json={"name": "Servicio Base 1", "defaultDurationMin": 30},
        headers=admin_h,
    ).json()
    s2 = auth_client.post(
        "/api/services",
        json={"name": "Servicio Base 2", "defaultDurationMin": 30},
        headers=admin_h,
    ).json()

    res = auth_client.put(
        f"/api/services/{s2['id']}",
        json={"name": "Servicio Base 1", "defaultDurationMin": 35},
        headers=admin_h,
    )
    assert res.status_code == 409


def test_update_service_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.put(
        f"/api/services/{FAKE_ID}",
        json={"name": "Fantasma", "defaultDurationMin": 30},
        headers=admin_h,
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Prestación no encontrada."}


def test_list_services_with_active_filter_true(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/services",
        json={"name": "Servicio A Desactivar", "defaultDurationMin": 30},
        headers=admin_h,
    ).json()
    srv_id = created["id"]
    auth_client.post(f"/api/services/{srv_id}/deactivate", headers=admin_h)

    res = auth_client.get("/api/services?active=true", headers=admin_h)
    assert res.status_code == 200
    assert all(s["id"] != srv_id for s in res.json())


def test_list_services_without_filter_includes_inactive_alphabetical(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s1 = auth_client.post("/api/services", json={"name": "Servicio Z", "defaultDurationMin": 30}, headers=admin_h).json()
    s2 = auth_client.post("/api/services", json={"name": "Servicio A", "defaultDurationMin": 30}, headers=admin_h).json()
    auth_client.post(f"/api/services/{s1['id']}/deactivate", headers=admin_h)

    res = auth_client.get("/api/services", headers=admin_h)
    assert res.status_code == 200
    names = [s["name"] for s in res.json()]
    assert any(s["id"] == s1["id"] for s in res.json())
    assert any(s["id"] == s2["id"] for s in res.json())
    lower_names = [n.lower() for n in names]
    assert lower_names == sorted(lower_names)


def test_reception_lists_services_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.get("/api/services", headers=rec_h)
    assert res.status_code == 200


def test_doctor_lists_services_responds_200(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.get("/api/services", headers=doc_h)
    assert res.status_code == 200


def test_detail_service_existing_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/services",
        json={"name": "Detalle Prestación", "defaultDurationMin": 25},
        headers=admin_h,
    ).json()
    srv_id = created["id"]

    res = auth_client.get(f"/api/services/{srv_id}", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["name"] == "Detalle Prestación"


def test_detail_service_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.get(f"/api/services/{FAKE_ID}", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Prestación no encontrada."}


def test_consult_services_without_token_responds_401(auth_client: TestClient) -> None:
    assert auth_client.get("/api/services").status_code == 401


def test_create_service_rejected_for_reception_403(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/services", json={"name": "S", "defaultDurationMin": 30}, headers=rec_h)
    assert res.status_code == 403


def test_create_service_rejected_for_doctor_403(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.post("/api/services", json={"name": "S", "defaultDurationMin": 30}, headers=doc_h)
    assert res.status_code == 403


def test_update_service_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post("/api/services", json={"name": "S ModR", "defaultDurationMin": 30}, headers=admin_h).json()
    srv_id = created["id"]

    res = auth_client.put(f"/api/services/{srv_id}", json={"name": "S Mod", "defaultDurationMin": 30}, headers=rec_h)
    assert res.status_code == 403


def test_update_service_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    created = auth_client.post("/api/services", json={"name": "S ModD", "defaultDurationMin": 30}, headers=admin_h).json()
    srv_id = created["id"]

    res = auth_client.put(f"/api/services/{srv_id}", json={"name": "S Mod", "defaultDurationMin": 30}, headers=doc_h)
    assert res.status_code == 403


def test_create_service_duplicate_name_responds_409(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    auth_client.post("/api/services", json={"name": "Prestación Única", "defaultDurationMin": 30}, headers=admin_h)
    res = auth_client.post("/api/services", json={"name": "Prestación Única", "defaultDurationMin": 30}, headers=admin_h)
    assert res.status_code == 409


def test_create_service_invalid_duration_responds_422(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/services", json={"name": "Prestación 0 min", "defaultDurationMin": 0}, headers=admin_h)
    assert res.status_code == 422


def test_create_service_empty_name_responds_422(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/services", json={"name": "", "defaultDurationMin": 30}, headers=admin_h)
    assert res.status_code == 422


def test_create_service_malformed_body_responds_400(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/services", json={"name": "S", "defaultDurationMin": 30, "extra": 123}, headers=admin_h)
    assert res.status_code == 400
