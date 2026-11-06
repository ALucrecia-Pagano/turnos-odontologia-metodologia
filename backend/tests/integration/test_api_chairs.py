from collections.abc import Iterator
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text

from tests.integration.auth_support import (
    LOGIN,
    OTHER_PROFESSIONAL_ID,
    PASSWORD,
    PROFESSIONAL_ID,
)

pytestmark = pytest.mark.integration

FAKE_ID = "00000000-0000-0000-0000-ffffffffffff"


@pytest.fixture(autouse=True)
def clean_chairs_table(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM chair"))
    yield



def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def test_create_chair_responds_201(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/chairs", json={"name": "Sillón Quirúrgico"}, headers=admin_h)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Sillón Quirúrgico"
    assert data["active"] is True


def test_update_chair_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post("/api/chairs", json={"name": "Sillón Odontopediatría"}, headers=admin_h).json()
    chair_id = created["id"]

    res = auth_client.put(f"/api/chairs/{chair_id}", json={"name": "Sillón Infantil Especial"}, headers=admin_h)
    assert res.status_code == 200
    assert res.json()["name"] == "Sillón Infantil Especial"


def test_update_chair_conserving_own_name_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post("/api/chairs", json={"name": "Sillón Panorámico"}, headers=admin_h).json()
    chair_id = created["id"]

    res = auth_client.put(f"/api/chairs/{chair_id}", json={"name": "Sillón Panorámico"}, headers=admin_h)
    assert res.status_code == 200
    assert res.json()["name"] == "Sillón Panorámico"


def test_update_chair_with_name_of_another_responds_409(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c1 = auth_client.post("/api/chairs", json={"name": "Sillón Principal"}, headers=admin_h).json()
    c2 = auth_client.post("/api/chairs", json={"name": "Sillón Secundario"}, headers=admin_h).json()

    res = auth_client.put(f"/api/chairs/{c2['id']}", json={"name": "Sillón Principal"}, headers=admin_h)
    assert res.status_code == 409


def test_update_chair_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.put(f"/api/chairs/{FAKE_ID}", json={"name": "Sillón Fantasma"}, headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Sillón no encontrado."}


def test_list_chairs_with_active_filter_true(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post("/api/chairs", json={"name": "Sillón Para Desactivar"}, headers=admin_h).json()
    chair_id = created["id"]
    auth_client.post(f"/api/chairs/{chair_id}/deactivate", headers=admin_h)

    res = auth_client.get("/api/chairs?active=true", headers=admin_h)
    assert res.status_code == 200
    assert all(c["id"] != chair_id for c in res.json())


def test_list_chairs_with_active_filter_false_returns_only_inactive(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post("/api/chairs", json={"name": "Sillón Inactivo Test"}, headers=admin_h).json()
    chair_id = created["id"]
    auth_client.post(f"/api/chairs/{chair_id}/deactivate", headers=admin_h)

    res = auth_client.get("/api/chairs?active=false", headers=admin_h)
    assert res.status_code == 200
    assert any(c["id"] == chair_id for c in res.json())
    assert all(c["active"] is False for c in res.json())


def test_list_chairs_without_filter_includes_inactive_alphabetical(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c1 = auth_client.post("/api/chairs", json={"name": "Sillón Z"}, headers=admin_h).json()
    c2 = auth_client.post("/api/chairs", json={"name": "Sillón A"}, headers=admin_h).json()
    auth_client.post(f"/api/chairs/{c1['id']}/deactivate", headers=admin_h)

    res = auth_client.get("/api/chairs", headers=admin_h)
    assert res.status_code == 200
    names = [c["name"] for c in res.json()]
    assert any(c["id"] == c1["id"] for c in res.json())
    assert any(c["id"] == c2["id"] for c in res.json())
    lower_names = [n.lower() for n in names]
    assert lower_names == sorted(lower_names)


def test_reception_lists_chairs_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.get("/api/chairs", headers=rec_h)
    assert res.status_code == 200


def test_doctor_lists_chairs_responds_200(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.get("/api/chairs", headers=doc_h)
    assert res.status_code == 200


def test_detail_chair_existing_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post("/api/chairs", json={"name": "Sillón Detalle"}, headers=admin_h).json()
    chair_id = created["id"]

    res = auth_client.get(f"/api/chairs/{chair_id}", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["name"] == "Sillón Detalle"


def test_detail_chair_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.get(f"/api/chairs/{FAKE_ID}", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Sillón no encontrado."}


def test_consult_chairs_without_token_responds_401(auth_client: TestClient) -> None:
    assert auth_client.get("/api/chairs").status_code == 401


def test_create_chair_rejected_for_reception_403(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/chairs", json={"name": "Sillón R"}, headers=rec_h)
    assert res.status_code == 403


def test_create_chair_rejected_for_doctor_403(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.post("/api/chairs", json={"name": "Sillón D"}, headers=doc_h)
    assert res.status_code == 403


def test_update_chair_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post("/api/chairs", json={"name": "Sillón ModR"}, headers=admin_h).json()
    chair_id = created["id"]

    res = auth_client.put(f"/api/chairs/{chair_id}", json={"name": "Sillón X"}, headers=rec_h)
    assert res.status_code == 403


def test_update_chair_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    created = auth_client.post("/api/chairs", json={"name": "Sillón ModD"}, headers=admin_h).json()
    chair_id = created["id"]

    res = auth_client.put(f"/api/chairs/{chair_id}", json={"name": "Sillón Y"}, headers=doc_h)
    assert res.status_code == 403


def test_create_chair_duplicate_name_responds_409(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    auth_client.post("/api/chairs", json={"name": "Sillón Unico 1"}, headers=admin_h)
    res = auth_client.post("/api/chairs", json={"name": "Sillón Unico 1"}, headers=admin_h)
    assert res.status_code == 409


def test_create_chair_empty_name_responds_422(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/chairs", json={"name": ""}, headers=admin_h)
    assert res.status_code == 422


def test_create_chair_malformed_body_responds_400(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/chairs", json={"name": "Sillón", "extra": 123}, headers=admin_h)
    assert res.status_code == 400
