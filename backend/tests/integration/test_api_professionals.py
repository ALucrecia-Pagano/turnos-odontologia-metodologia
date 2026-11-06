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
def clean_professionals_table(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM professional WHERE id NOT IN (:first, :second)"),
            {"first": PROFESSIONAL_ID, "second": OTHER_PROFESSIONAL_ID},
        )
    yield



def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def test_create_professional_with_license_responds_201(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(
        "/api/professionals",
        json={"fullName": "Dr. Fernando Torres", "licenseNumber": "MN 11223"},
        headers=admin_h,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["fullName"] == "Dr. Fernando Torres"
    assert data["licenseNumber"] == "MN 11223"
    assert data["active"] is True


def test_update_professional_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/professionals",
        json={"fullName": "Dra. Natalia Morales", "licenseNumber": "MN 33445"},
        headers=admin_h,
    ).json()
    prof_id = created["id"]

    res = auth_client.put(
        f"/api/professionals/{prof_id}",
        json={"fullName": "Dra. Natalia Morales Ramos", "licenseNumber": "MN 33445-B"},
        headers=admin_h,
    )
    assert res.status_code == 200
    assert res.json()["fullName"] == "Dra. Natalia Morales Ramos"
    assert res.json()["licenseNumber"] == "MN 33445-B"


def test_update_professional_conserving_own_name_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/professionals",
        json={"fullName": "Dr. Pablo Rossi", "licenseNumber": "MN 44556"},
        headers=admin_h,
    ).json()
    prof_id = created["id"]

    res = auth_client.put(
        f"/api/professionals/{prof_id}",
        json={"fullName": "Dr. Pablo Rossi", "licenseNumber": "MN 44556-C"},
        headers=admin_h,
    )
    assert res.status_code == 200
    assert res.json()["licenseNumber"] == "MN 44556-C"


def test_update_professional_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.put(
        f"/api/professionals/{FAKE_ID}",
        json={"fullName": "Dr. Fantasma"},
        headers=admin_h,
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


def test_list_professionals_with_active_filter_true(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/professionals",
        json={"fullName": "Dr. Temporal Activo"},
        headers=admin_h,
    ).json()
    prof_id = created["id"]
    auth_client.post(f"/api/professionals/{prof_id}/deactivate", headers=admin_h)

    res = auth_client.get("/api/professionals?active=true", headers=admin_h)
    assert res.status_code == 200
    assert all(p["id"] != prof_id for p in res.json())


def test_list_professionals_without_filter_includes_inactive_alphabetical(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    p1 = auth_client.post("/api/professionals", json={"fullName": "Dr. Zenon Test"}, headers=admin_h).json()
    p2 = auth_client.post("/api/professionals", json={"fullName": "Dr. Zulma Test"}, headers=admin_h).json()
    auth_client.post(f"/api/professionals/{p1['id']}/deactivate", headers=admin_h)

    res = auth_client.get("/api/professionals", headers=admin_h)
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert p1["id"] in ids
    assert p2["id"] in ids
    assert ids.index(p1["id"]) < ids.index(p2["id"])


def test_reception_lists_professionals_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.get("/api/professionals", headers=rec_h)
    assert res.status_code == 200


def test_doctor_lists_professionals_responds_200(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.get("/api/professionals", headers=doc_h)
    assert res.status_code == 200


def test_detail_professional_existing_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    created = auth_client.post(
        "/api/professionals",
        json={"fullName": "Dra. Lucia Gimenez", "licenseNumber": "MN 77889"},
        headers=admin_h,
    ).json()
    prof_id = created["id"]

    res = auth_client.get(f"/api/professionals/{prof_id}", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["fullName"] == "Dra. Lucia Gimenez"
    assert res.json()["licenseNumber"] == "MN 77889"


def test_detail_professional_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.get(f"/api/professionals/{FAKE_ID}", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


def test_consult_professionals_without_token_responds_401(auth_client: TestClient) -> None:
    assert auth_client.get("/api/professionals").status_code == 401


def test_create_professional_rejected_for_reception_403(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/professionals", json={"fullName": "Dr. No"}, headers=rec_h)
    assert res.status_code == 403


def test_create_professional_rejected_for_doctor_403(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.post("/api/professionals", json={"fullName": "Dr. No"}, headers=doc_h)
    assert res.status_code == 403


def test_update_professional_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post("/api/professionals", json={"fullName": "Dr. P"}, headers=admin_h).json()
    prof_id = created["id"]

    res = auth_client.put(f"/api/professionals/{prof_id}", json={"fullName": "Dr. Mod"}, headers=rec_h)
    assert res.status_code == 403


def test_update_professional_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    created = auth_client.post("/api/professionals", json={"fullName": "Dr. P2"}, headers=admin_h).json()
    prof_id = created["id"]

    res = auth_client.put(f"/api/professionals/{prof_id}", json={"fullName": "Dr. Mod"}, headers=doc_h)
    assert res.status_code == 403


def test_create_professional_empty_name_responds_422(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/professionals", json={"fullName": ""}, headers=admin_h)
    assert res.status_code == 422


def test_create_professional_malformed_body_responds_400(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post("/api/professionals", json={"fullName": "Dr. Ok", "extra": 123}, headers=admin_h)
    assert res.status_code == 400
