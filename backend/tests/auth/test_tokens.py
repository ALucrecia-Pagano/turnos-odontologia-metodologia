from datetime import UTC, datetime
from uuid import UUID

import jwt
from pydantic import SecretStr

from app.auth.model import AuthenticatedUser
from app.auth.tokens import TokenClaims, create_access_token, decode_access_token
from app.config import Settings
from app.domain.model import Role


SECRET = "secreto-ficticio-de-32-caractere"
USER = AuthenticatedUser(
    id=UUID("00000000-0000-0000-0000-0000000000e2"),
    username="recepcion",
    display_name="Recepción de Prueba",
    role=Role.RECEPCION,
    professional_id=None,
)


def token_settings() -> Settings:
    return Settings(
        app_env="test",
        api_port=8000,
        postgres_user="test_user",
        postgres_password="test_password",
        postgres_db="test_db",
        database_url="postgresql+psycopg://test_user:test_password@localhost:5432/test_db",
        redis_url="redis://localhost:6379/0",
        jwt_secret=SecretStr(SECRET),
        jwt_algorithm="HS256",
        jwt_expires_min=60,
        seed_user_password=None,
        app_timezone="America/Argentina/Buenos_Aires",
        cors_origin="http://localhost:5173",
        vite_api_url="http://localhost:8000/api",
    )


def test_token_has_exact_claims() -> None:
    now = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)

    token = create_access_token(USER, token_settings(), now)

    payload = jwt.decode(token, options={"verify_signature": False})
    assert set(payload) == {"sub", "role", "exp"}
    assert payload["sub"] == str(USER.id)
    assert payload["role"] == "recepcion"
    assert payload["exp"] == int(datetime(2026, 11, 5, 13, 0, tzinfo=UTC).timestamp())


def test_decode_accepts_token_with_current_now() -> None:
    settings = token_settings()

    token = create_access_token(USER, settings, datetime.now(UTC))

    assert decode_access_token(token, settings) == TokenClaims(
        user_id=USER.id, role=Role.RECEPCION
    )
