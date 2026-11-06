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
def clean_deactivation_tables(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM service"))
        conn.execute(text("DELETE FROM chair"))
        conn.execute(
            text("DELETE FROM professional WHERE id NOT IN (:first, :second)"),
            {"first": PROFESSIONAL_ID, "second": OTHER_PROFESSIONAL_ID},
        )
    yield



def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


# --- Profesionales (Scenarios 79-88) ---


def test_deactivate_professional_active_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. Activo P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_professional_inactive_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. Inactivo P"}, headers=admin_h).json()
    auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/professionals/{p['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_professional_already_inactive_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. Doble Inactivo P"}, headers=admin_h).json()
    auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_professional_already_active_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. Ya Activo P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_professional_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/professionals/{FAKE_ID}/deactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


def test_reactivate_professional_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/professionals/{FAKE_ID}/reactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Profesional no encontrado."}


def test_deactivate_professional_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. R403 P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=rec_h)
    assert res.status_code == 403


def test_deactivate_professional_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. D403 P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/deactivate", headers=doc_h)
    assert res.status_code == 403


def test_reactivate_professional_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. RReact403 P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/reactivate", headers=rec_h)
    assert res.status_code == 403


def test_reactivate_professional_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    p = auth_client.post("/api/professionals", json={"fullName": "Dr. DReact403 P"}, headers=admin_h).json()
    res = auth_client.post(f"/api/professionals/{p['id']}/reactivate", headers=doc_h)
    assert res.status_code == 403


# --- Sillones (Scenarios 89-98) ---


def test_deactivate_chair_active_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c = auth_client.post("/api/chairs", json={"name": "Sillón Activo C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_chair_inactive_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c = auth_client.post("/api/chairs", json={"name": "Sillón Inactivo C"}, headers=admin_h).json()
    auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/chairs/{c['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_chair_already_inactive_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c = auth_client.post("/api/chairs", json={"name": "Sillón Doble Inactivo C"}, headers=admin_h).json()
    auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_chair_already_active_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    c = auth_client.post("/api/chairs", json={"name": "Sillón Ya Activo C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_chair_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/chairs/{FAKE_ID}/deactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Sillón no encontrado."}


def test_reactivate_chair_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/chairs/{FAKE_ID}/reactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Sillón no encontrado."}


def test_deactivate_chair_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    c = auth_client.post("/api/chairs", json={"name": "Sillón R403 C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=rec_h)
    assert res.status_code == 403


def test_deactivate_chair_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    c = auth_client.post("/api/chairs", json={"name": "Sillón D403 C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/deactivate", headers=doc_h)
    assert res.status_code == 403


def test_reactivate_chair_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    c = auth_client.post("/api/chairs", json={"name": "Sillón RReact403 C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/reactivate", headers=rec_h)
    assert res.status_code == 403


def test_reactivate_chair_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    c = auth_client.post("/api/chairs", json={"name": "Sillón DReact403 C"}, headers=admin_h).json()
    res = auth_client.post(f"/api/chairs/{c['id']}/reactivate", headers=doc_h)
    assert res.status_code == 403


# --- Prestaciones (Scenarios 99-108) ---


def test_deactivate_service_active_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s = auth_client.post("/api/services", json={"name": "Prestación Activa S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_service_inactive_responds_200(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s = auth_client.post("/api/services", json={"name": "Prestación Inactiva S", "defaultDurationMin": 30}, headers=admin_h).json()
    auth_client.post(f"/api/services/{s['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/services/{s['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_service_already_inactive_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s = auth_client.post("/api/services", json={"name": "Prestación Doble Inactiva S", "defaultDurationMin": 30}, headers=admin_h).json()
    auth_client.post(f"/api/services/{s['id']}/deactivate", headers=admin_h)
    res = auth_client.post(f"/api/services/{s['id']}/deactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is False


def test_reactivate_service_already_active_responds_200_no_changes(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    s = auth_client.post("/api/services", json={"name": "Prestación Ya Activa S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/reactivate", headers=admin_h)
    assert res.status_code == 200
    assert res.json()["active"] is True


def test_deactivate_service_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/services/{FAKE_ID}/deactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Prestación no encontrada."}


def test_reactivate_service_nonexistent_responds_404(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/services/{FAKE_ID}/reactivate", headers=admin_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Prestación no encontrada."}


def test_deactivate_service_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    s = auth_client.post("/api/services", json={"name": "Prestación R403 S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/deactivate", headers=rec_h)
    assert res.status_code == 403


def test_deactivate_service_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    s = auth_client.post("/api/services", json={"name": "Prestación D403 S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/deactivate", headers=doc_h)
    assert res.status_code == 403


def test_reactivate_service_rejected_for_reception_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    rec_h = token_for(auth_client, "recepcion")
    s = auth_client.post("/api/services", json={"name": "Prestación RReact403 S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/reactivate", headers=rec_h)
    assert res.status_code == 403


def test_reactivate_service_rejected_for_doctor_403(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    doc_h = token_for(auth_client, "odontologo")
    s = auth_client.post("/api/services", json={"name": "Prestación DReact403 S", "defaultDurationMin": 30}, headers=admin_h).json()
    res = auth_client.post(f"/api/services/{s['id']}/reactivate", headers=doc_h)
    assert res.status_code == 403
