from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy.engine import URL

from app.api.deps import Permission, require_permission
from app.auth.permissions import Action, Resource
from app.config import load_settings
from app.db.session import create_database_engine
from app.main import create_app
from tests.auth.rbac_matrix import ALL, DENIED, MATRIX, OWN, ROLES, MatrixRow
from tests.integration.auth_support import (
    LOGIN,
    PASSWORD,
    create_auth_users,
    remove_auth_users,
)


pytestmark = pytest.mark.integration

EXPECTED_SCOPE = {ALL: "ALL", OWN: "OWN"}


@dataclass(frozen=True)
class MatrixClient:
    client: TestClient
    headers: dict[str, dict[str, str]]

    def call(self, resource: str, action: str, role: str) -> httpx.Response:
        response: httpx.Response = self.client.get(
            route_path(resource, action), headers=self.headers[role]
        )
        return response


def route_path(resource: str, action: str) -> str:
    return f"/api/test-rbac/{resource}/{action}"


def mount_route(router: APIRouter, row: MatrixRow) -> None:
    dependency = require_permission(Resource[row.resource], Action[row.action])

    @router.get(route_path(row.resource, row.action))
    def matrix_route(
        permission: Annotated[Permission, Depends(dependency)],
    ) -> dict[str, str]:
        return {"scope": permission.scope.name, "role": permission.actor.role.value}


@pytest.fixture(scope="module")
def matrix(test_database_url: URL) -> Iterator[MatrixClient]:
    settings = load_settings().model_copy(
        update={"database_url": test_database_url.render_as_string(hide_password=False)}
    )
    engine = create_database_engine(settings)
    create_auth_users(engine)
    app = create_app(settings)
    router = APIRouter()
    for row in MATRIX:
        mount_route(router, row)
    app.include_router(router)
    client = TestClient(app)
    headers: dict[str, dict[str, str]] = {}
    for role in ROLES:
        response = client.post(LOGIN, json={"username": role, "password": PASSWORD})
        assert response.status_code == 200
        headers[role] = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    try:
        yield MatrixClient(client, headers)
    finally:
        app.state.engine.dispose()
        remove_auth_users(engine)
        engine.dispose()


@pytest.mark.parametrize(
    ("row", "role"),
    [(row, role) for row in MATRIX for role in ROLES],
    ids=[f"{row.resource}-{row.action}-{role}" for row in MATRIX for role in ROLES],
)
def test_matrix_cell_over_http(row: MatrixRow, role: str, matrix: MatrixClient) -> None:
    response = matrix.call(row.resource, row.action, role)

    cell = row.cell(role)
    if cell == DENIED:
        assert response.status_code == 403
        assert response.json() == {
            "violations": [
                {
                    "code": "FORBIDDEN_OPERATION",
                    "message": f"No tiene permiso para {row.message}.",
                }
            ]
        }
    else:
        assert response.status_code == 200
        assert response.json() == {"scope": EXPECTED_SCOPE[cell], "role": role}


def test_doctor_cannot_book(matrix: MatrixClient) -> None:
    response = matrix.call("APPOINTMENT", "CREATE", "odontologo")

    assert response.status_code == 403
    violations = response.json()["violations"]
    assert len(violations) == 1
    assert violations[0]["code"] == "FORBIDDEN_OPERATION"
    assert violations[0]["message"] == "No tiene permiso para dar turnos."


def test_reception_cannot_create_professional(matrix: MatrixClient) -> None:
    response = matrix.call("PROFESSIONAL", "CREATE", "recepcion")

    assert response.status_code == 403
    assert response.json()["violations"][0]["message"] == (
        "No tiene permiso para crear profesionales."
    )


def test_nobody_deletes_patients(matrix: MatrixClient) -> None:
    assert matrix.call("PATIENT", "DELETE", "administrador").status_code == 403


def test_doctor_scope_own_on_working_hours(matrix: MatrixClient) -> None:
    response = matrix.call("WORKING_HOURS", "UPDATE", "odontologo")

    assert response.status_code == 200
    assert response.json()["scope"] == "OWN"


def test_admin_scope_all_on_working_hours(matrix: MatrixClient) -> None:
    response = matrix.call("WORKING_HOURS", "UPDATE", "administrador")

    assert response.status_code == 200
    assert response.json()["scope"] == "ALL"


def test_doctor_scope_all_on_agenda(matrix: MatrixClient) -> None:
    response = matrix.call("APPOINTMENT", "READ_AGENDA", "odontologo")

    assert response.status_code == 200
    assert response.json()["scope"] == "ALL"
