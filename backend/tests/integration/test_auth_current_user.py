from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import Engine, text

from app.auth.model import AuthenticatedUser
from app.auth.tokens import create_access_token
from app.config import Settings
from app.domain.model import Actor, Role
from tests.integration.auth_support import (
    ADMIN_ID,
    DOCTOR_ID,
    INVALID_TOKEN_BODY,
    LOGIN,
    ME,
    OTHER_PROFESSIONAL_ID,
    PASSWORD,
    PROFESSIONAL_ID,
    RECEPTION_ID,
)


pytestmark = pytest.mark.integration

ACTOR_ROUTE = "/api/test-actor"


def login_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(LOGIN, json={"username": username, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def execute(engine: Engine, statement: str, **parameters: object) -> None:
    with engine.begin() as connection:
        connection.execute(text(statement), parameters)


def test_valid_token_is_accepted(auth_client: TestClient, auth_settings: Settings) -> None:
    user = AuthenticatedUser(
        id=RECEPTION_ID,
        username="recepcion",
        display_name="Usuario Ficticio recepcion",
        role=Role.RECEPCION,
        professional_id=None,
    )
    # Armado igual que un token vencido, pero con el now actual (D14).
    token = create_access_token(user, auth_settings, datetime.now(UTC))

    response = auth_client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_unknown_user_with_valid_token_is_rejected(
    auth_client: TestClient, auth_settings: Settings
) -> None:
    user = AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-00000000dead"),
        username="nadie",
        display_name="Nadie",
        role=Role.RECEPCION,
        professional_id=None,
    )
    token = create_access_token(user, auth_settings, datetime.now(UTC))

    response = auth_client.get(ME, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


def test_deactivated_user_with_valid_token_is_rejected(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = login_headers(auth_client, "recepcion")
    execute(test_engine, "UPDATE app_user SET active = false WHERE id = :id", id=RECEPTION_ID)

    response = auth_client.get(ME, headers=headers)

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


def test_role_changed_user_with_valid_token_is_rejected(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = login_headers(auth_client, "recepcion")
    execute(
        test_engine,
        "UPDATE app_user SET role = 'administrador' WHERE id = :id",
        id=RECEPTION_ID,
    )

    response = auth_client.get(ME, headers=headers)

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


def test_new_login_after_role_change_has_new_role(
    auth_client: TestClient, test_engine: Engine
) -> None:
    execute(
        test_engine,
        "UPDATE app_user SET role = 'administrador' WHERE id = :id",
        id=RECEPTION_ID,
    )

    response = auth_client.get(ME, headers=login_headers(auth_client, "recepcion"))

    assert response.status_code == 200
    assert response.json()["role"] == "administrador"


def test_reactivated_user_with_valid_token_is_accepted(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = login_headers(auth_client, "recepcion")
    execute(test_engine, "UPDATE app_user SET active = false WHERE id = :id", id=RECEPTION_ID)
    assert auth_client.get(ME, headers=headers).status_code == 401
    execute(test_engine, "UPDATE app_user SET active = true WHERE id = :id", id=RECEPTION_ID)

    response = auth_client.get(ME, headers=headers)

    assert response.status_code == 200


def test_professional_change_with_valid_token_is_accepted(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = login_headers(auth_client, "odontologo")
    execute(
        test_engine,
        "UPDATE app_user SET professional_id = :professional_id WHERE id = :id",
        professional_id=OTHER_PROFESSIONAL_ID,
        id=DOCTOR_ID,
    )

    response = auth_client.get(ME, headers=headers)

    assert response.status_code == 200
    assert response.json()["professionalId"] == str(OTHER_PROFESSIONAL_ID)


def test_me_for_doctor(auth_client: TestClient) -> None:
    response = auth_client.get(ME, headers=login_headers(auth_client, "odontologo"))

    assert response.status_code == 200
    assert response.json() == {
        "id": str(DOCTOR_ID),
        "username": "odontologo",
        "displayName": "Usuario Ficticio odontologo",
        "role": "odontologo",
        "professionalId": str(PROFESSIONAL_ID),
    }


def test_me_for_reception(auth_client: TestClient) -> None:
    response = auth_client.get(ME, headers=login_headers(auth_client, "recepcion"))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(RECEPTION_ID)
    assert body["role"] == "recepcion"
    assert body["professionalId"] is None


def test_me_for_admin(auth_client: TestClient) -> None:
    response = auth_client.get(ME, headers=login_headers(auth_client, "administrador"))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(ADMIN_ID)
    assert body["role"] == "administrador"
    assert body["professionalId"] is None


def test_login_with_inactive_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    execute(
        test_engine,
        "UPDATE professional SET active = false WHERE id = :id",
        id=PROFESSIONAL_ID,
    )

    response = auth_client.post(LOGIN, json={"username": "odontologo", "password": PASSWORD})

    assert response.status_code == 200


def test_me_with_inactive_professional(
    auth_client: TestClient, test_engine: Engine
) -> None:
    headers = login_headers(auth_client, "odontologo")
    execute(
        test_engine,
        "UPDATE professional SET active = false WHERE id = :id",
        id=PROFESSIONAL_ID,
    )

    response = auth_client.get(ME, headers=headers)

    assert response.status_code == 200


def mount_actor_route(app: FastAPI) -> None:
    from app.api.deps import get_current_actor

    router = APIRouter()

    @router.get(ACTOR_ROUTE)
    def actor_route(
        actor: Annotated[Actor, Depends(get_current_actor)],
    ) -> dict[str, str | None]:
        return {
            "user_id": str(actor.user_id),
            "role": actor.role.name,
            "professional_id": (
                str(actor.professional_id) if actor.professional_id is not None else None
            ),
        }

    app.include_router(router)


def test_actor_for_doctor(auth_app: FastAPI, auth_client: TestClient) -> None:
    mount_actor_route(auth_app)

    response = auth_client.get(ACTOR_ROUTE, headers=login_headers(auth_client, "odontologo"))

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "user_id": str(DOCTOR_ID),
        "role": "ODONTOLOGO",
        "professional_id": str(PROFESSIONAL_ID),
    }
    assert body["user_id"] != body["professional_id"]


def test_actor_for_reception(auth_app: FastAPI, auth_client: TestClient) -> None:
    mount_actor_route(auth_app)

    response = auth_client.get(ACTOR_ROUTE, headers=login_headers(auth_client, "recepcion"))

    assert response.json() == {
        "user_id": str(RECEPTION_ID),
        "role": "RECEPCION",
        "professional_id": None,
    }


def test_actor_for_admin(auth_app: FastAPI, auth_client: TestClient) -> None:
    mount_actor_route(auth_app)

    response = auth_client.get(
        ACTOR_ROUTE, headers=login_headers(auth_client, "administrador")
    )

    assert response.json() == {
        "user_id": str(ADMIN_ID),
        "role": "ADMINISTRADOR",
        "professional_id": None,
    }


def test_client_header_does_not_change_actor(
    auth_app: FastAPI, auth_client: TestClient
) -> None:
    mount_actor_route(auth_app)
    headers = login_headers(auth_client, "recepcion")

    response = auth_client.get(ACTOR_ROUTE, headers={**headers, "X-Role": "administrador"})

    assert response.json()["role"] == "RECEPCION"


def test_health_without_token(auth_client: TestClient) -> None:
    response = auth_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
