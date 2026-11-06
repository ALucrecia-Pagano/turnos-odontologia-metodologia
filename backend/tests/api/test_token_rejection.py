from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import socket
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
import jwt
import pytest

from app.api.deps import get_current_user
from app.auth.model import AuthenticatedUser
from app.auth.tokens import create_access_token
from app.config import Settings
from app.domain.model import Role
from app.main import create_app


INVALID_TOKEN_BODY = {
    "code": "INVALID_TOKEN",
    "message": "La sesión venció o no es válida. Inicie sesión de nuevo.",
}
USER = AuthenticatedUser(
    id=UUID("00000000-0000-0000-0000-0000000000e2"),
    username="recepcion",
    display_name="Recepción de Prueba",
    role=Role.RECEPCION,
    professional_id=None,
)
OTHER_SECRET = "otro-secreto-ficticio-de-32-caracteres"
FUTURE = datetime(2099, 1, 1, tzinfo=UTC)


def closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


@pytest.fixture
def dead_settings(api_settings: Settings) -> Settings:
    return api_settings.model_copy(
        update={
            "database_url": (
                f"postgresql+psycopg://test_user:test_password@127.0.0.1:{closed_port()}/test_db"
            )
        }
    )


@pytest.fixture
def client(dead_settings: Settings) -> TestClient:
    app = create_app(dead_settings)
    router = APIRouter()

    @router.get("/api/protected", dependencies=[Depends(get_current_user)])
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return TestClient(app)


def secret_of(settings: Settings) -> str:
    return settings.jwt_secret.get_secret_value()


def claims(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "sub": str(USER.id),
        "role": "recepcion",
        "exp": int(FUTURE.timestamp()),
    }
    base.update(overrides)
    return {key: value for key, value in base.items() if value is not None}


def header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def tampered_payload_token(settings: Settings) -> str:
    original = jwt.encode(claims(), secret_of(settings), algorithm="HS256")
    forged = jwt.encode(claims(role="administrador"), secret_of(settings), algorithm="HS256")
    head, _, signature = original.split(".")
    return ".".join((head, forged.split(".")[1], signature))


def tampered_signature_token(settings: Settings) -> str:
    original = jwt.encode(claims(), secret_of(settings), algorithm="HS256")
    head, payload, signature = original.split(".")
    # El PRIMER caracter: los bits finales de una firma base64url no siempre se usan.
    replacement = "A" if signature[0] != "A" else "B"
    return ".".join((head, payload, replacement + signature[1:]))


def expired_one_second_token(settings: Settings) -> str:
    # Emitido por el codigo de produccion: exp queda un segundo antes del reloj real.
    issued_at = datetime.now(UTC) - timedelta(minutes=settings.jwt_expires_min, seconds=1)
    return create_access_token(USER, settings, issued_at)


HeaderBuilder = Callable[[Settings], dict[str, str]]

REJECTED_HEADERS: dict[str, HeaderBuilder] = {
    "no_header": lambda settings: {},
    "empty_bearer": lambda settings: {"Authorization": "Bearer "},
    "basic_scheme": lambda settings: {"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="},
    "garbage": lambda settings: header("no-es-un-token"),
    "expired_years": lambda settings: header(
        create_access_token(USER, settings, datetime(2020, 1, 1, tzinfo=UTC))
    ),
    "expired_one_second": lambda settings: header(expired_one_second_token(settings)),
    "tampered_payload": lambda settings: header(tampered_payload_token(settings)),
    "tampered_signature": lambda settings: header(tampered_signature_token(settings)),
    "other_key": lambda settings: header(
        jwt.encode(claims(), OTHER_SECRET, algorithm="HS256")
    ),
    "alg_none": lambda settings: header(jwt.encode(claims(), "", algorithm="none")),
    "other_algorithm": lambda settings: header(
        jwt.encode(claims(), secret_of(settings), algorithm="HS512")
    ),
    "missing_exp": lambda settings: header(
        jwt.encode(
            {"sub": str(USER.id), "role": "recepcion"},
            secret_of(settings),
            algorithm="HS256",
        )
    ),
    "missing_sub": lambda settings: header(
        jwt.encode(
            {"role": "recepcion", "exp": int(FUTURE.timestamp())},
            secret_of(settings),
            algorithm="HS256",
        )
    ),
    "missing_role": lambda settings: header(
        jwt.encode(
            {"sub": str(USER.id), "exp": int(FUTURE.timestamp())},
            secret_of(settings),
            algorithm="HS256",
        )
    ),
    "sub_not_uuid": lambda settings: header(
        jwt.encode(claims(sub="no-es-uuid"), secret_of(settings), algorithm="HS256")
    ),
    "unknown_role": lambda settings: header(
        jwt.encode(claims(role="superusuario"), secret_of(settings), algorithm="HS256")
    ),
}


@pytest.mark.parametrize(
    "case",
    [
        "no_header",
        "empty_bearer",
        "basic_scheme",
        "garbage",
        "token_in_url",
        "expired_years",
        "expired_one_second",
        "tampered_payload",
        "tampered_signature",
        "other_key",
        "alg_none",
        "other_algorithm",
        "missing_exp",
        "missing_sub",
        "missing_role",
        "sub_not_uuid",
        "unknown_role",
    ],
)
def test_rejected_token(case: str, client: TestClient, dead_settings: Settings) -> None:
    if case == "token_in_url":
        token = create_access_token(USER, dead_settings, datetime.now(UTC))
        response = client.get(f"/api/protected?token={token}")
    else:
        response = client.get("/api/protected", headers=REJECTED_HEADERS[case](dead_settings))

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_expired_token_does_not_open_database_connection(
    client: TestClient, dead_settings: Settings
) -> None:
    token = create_access_token(USER, dead_settings, datetime(2020, 1, 1, tzinfo=UTC))

    # Contra un puerto cerrado, cualquier consulta terminaria en un error de conexion.
    response = client.get("/api/protected", headers=header(token))

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY


def test_no_token_on_permission_route(dead_settings: Settings) -> None:
    from app.api.deps import require_permission
    from app.auth.permissions import Action, Resource

    app = create_app(dead_settings)
    router = APIRouter()

    @router.post(
        "/api/permission-route",
        dependencies=[Depends(require_permission(Resource.APPOINTMENT, Action.CREATE))],
    )
    def permission_route() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)

    response = TestClient(app).post("/api/permission-route")

    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN_BODY
