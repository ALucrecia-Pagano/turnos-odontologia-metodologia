from collections.abc import Iterator
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text

from tests.integration.auth_support import LOGIN, PASSWORD

pytestmark = pytest.mark.integration

FAKE_ID = "00000000-0000-0000-0000-ffffffffffff"


@pytest.fixture(autouse=True)
def clean_patients_table(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM patient"))
    yield



def token_for(client: TestClient, role: str) -> dict[str, str]:
    res = client.post(LOGIN, json={"username": role, "password": PASSWORD})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['accessToken']}"}


def test_create_patient_by_reception_responds_201(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post(
        "/api/patients",
        json={"fullName": "Valeria Castro", "dni": "35.111.222", "phone": "11556677", "healthInsurance": "OSDE"},
        headers=rec_h,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["fullName"] == "Valeria Castro"
    assert data["dni"] == "35111222"


def test_create_patient_by_admin_responds_201(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(
        "/api/patients",
        json={"fullName": "Esteban Quito", "dni": "35.222.333"},
        headers=admin_h,
    )
    assert res.status_code == 201
    assert res.json()["dni"] == "35222333"


def test_update_patient_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Federico Diaz", "dni": "35.333.444"},
        headers=rec_h,
    ).json()
    p_id = created["id"]

    res = auth_client.put(
        f"/api/patients/{p_id}",
        json={"fullName": "Federico Diaz Acosta", "dni": "35.333.444", "healthInsurance": "Swiss Medical"},
        headers=rec_h,
    )
    assert res.status_code == 200
    assert res.json()["fullName"] == "Federico Diaz Acosta"
    assert res.json()["healthInsurance"] == "Swiss Medical"


def test_update_patient_conserving_own_dni_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Gisela Suarez", "dni": "35.444.555", "phone": "1122"},
        headers=rec_h,
    ).json()
    p_id = created["id"]

    res = auth_client.put(
        f"/api/patients/{p_id}",
        json={"fullName": "Gisela Suarez", "dni": "35444555", "phone": "9988"},
        headers=rec_h,
    )
    assert res.status_code == 200
    assert res.json()["phone"] == "9988"


def test_update_patient_with_dni_of_another_responds_409(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    p1 = auth_client.post("/api/patients", json={"fullName": "P1", "dni": "35.555.666"}, headers=rec_h).json()
    p2 = auth_client.post("/api/patients", json={"fullName": "P2", "dni": "35.666.777"}, headers=rec_h).json()

    res = auth_client.put(
        f"/api/patients/{p2['id']}",
        json={"fullName": "P2 Mod", "dni": "35.555.666"},
        headers=rec_h,
    )
    assert res.status_code == 409


def test_update_patient_nonexistent_responds_404(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.put(
        f"/api/patients/{FAKE_ID}",
        json={"fullName": "Fantasma", "dni": "35.777.888"},
        headers=rec_h,
    )
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Paciente no encontrado."}


def test_search_patients_by_name_part(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Ana Pérez", "dni": "35.888.999"},
        headers=rec_h,
    ).json()

    res = auth_client.get("/api/patients?query=pérez", headers=rec_h)
    assert res.status_code == 200
    assert any(p["id"] == created["id"] for p in res.json())


def test_search_patients_without_accent_does_not_find_accented_name(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Ana Pérez", "dni": "35.888.998"},
        headers=rec_h,
    ).json()

    res = auth_client.get("/api/patients?query=perez", headers=rec_h)
    assert res.status_code == 200
    assert all(p["id"] != created["id"] for p in res.json())


def test_search_patients_by_dni_prefix(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Mariano Moreno", "dni": "35.999.001"},
        headers=rec_h,
    ).json()

    res = auth_client.get("/api/patients?query=35999", headers=rec_h)
    assert res.status_code == 200
    assert any(p["id"] == created["id"] for p in res.json())


def test_doctor_lists_patients_responds_200(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.get("/api/patients", headers=doc_h)
    assert res.status_code == 200


def test_detail_patient_existing_responds_200(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    created = auth_client.post(
        "/api/patients",
        json={"fullName": "Claudia Lopez", "dni": "36.111.222"},
        headers=rec_h,
    ).json()
    p_id = created["id"]

    res = auth_client.get(f"/api/patients/{p_id}", headers=rec_h)
    assert res.status_code == 200
    assert res.json()["fullName"] == "Claudia Lopez"


def test_detail_patient_nonexistent_responds_404(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.get(f"/api/patients/{FAKE_ID}", headers=rec_h)
    assert res.status_code == 404
    assert res.json() == {"code": "NOT_FOUND", "message": "Paciente no encontrado."}


def test_consult_patients_without_token_responds_401(auth_client: TestClient) -> None:
    assert auth_client.get("/api/patients").status_code == 401


def test_create_patient_rejected_for_doctor_403(auth_client: TestClient) -> None:
    doc_h = token_for(auth_client, "odontologo")
    res = auth_client.post("/api/patients", json={"fullName": "P", "dni": "36.222.333"}, headers=doc_h)
    assert res.status_code == 403


def test_update_patient_rejected_for_doctor_403(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    doc_h = token_for(auth_client, "odontologo")
    created = auth_client.post("/api/patients", json={"fullName": "P", "dni": "36.333.444"}, headers=rec_h).json()
    p_id = created["id"]

    res = auth_client.put(f"/api/patients/{p_id}", json={"fullName": "P Mod", "dni": "36.333.444"}, headers=doc_h)
    assert res.status_code == 403


def test_create_patient_duplicate_dni_responds_409(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    auth_client.post("/api/patients", json={"fullName": "P Original", "dni": "36.444.555"}, headers=rec_h)
    res = auth_client.post("/api/patients", json={"fullName": "P Repetido", "dni": "36.444.555"}, headers=rec_h)
    assert res.status_code == 409


def test_create_patient_invalid_dni_format_responds_422(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/patients", json={"fullName": "P", "dni": "123"}, headers=rec_h)
    assert res.status_code == 422


def test_create_patient_empty_name_responds_422(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/patients", json={"fullName": "", "dni": "36.555.666"}, headers=rec_h)
    assert res.status_code == 422


def test_create_patient_malformed_body_responds_400(auth_client: TestClient) -> None:
    rec_h = token_for(auth_client, "recepcion")
    res = auth_client.post("/api/patients", json={"fullName": "P", "dni": "36.666.777", "extra": 1}, headers=rec_h)
    assert res.status_code == 400


def test_patient_deactivation_does_not_exist_in_api(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.post(f"/api/patients/{FAKE_ID}/deactivate", headers=admin_h)
    assert res.status_code == 404


def test_patient_deletion_does_not_exist_in_api(auth_client: TestClient) -> None:
    admin_h = token_for(auth_client, "administrador")
    res = auth_client.delete(f"/api/patients/{FAKE_ID}", headers=admin_h)
    assert res.status_code == 405
